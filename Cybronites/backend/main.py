from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import datetime
import json
import logging
import uuid
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

# Local imports
from .blockchain import Blockchain, Block
from .ml_engine import MLEngine
from .models import get_model_parameters
from .database import engine, SessionLocal, get_db
from . import db_models

# Initialize DB
db_models.Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
app = FastAPI(title="AI Guardian Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Engines
blockchain = Blockchain()
ml_engine = MLEngine()

# Global State
def get_initial_round_id():
    db = SessionLocal()
    last_id = db.query(func.max(db_models.Round.id)).scalar()
    db.close()
    return last_id if last_id else 0

current_round_id = get_initial_round_id()
round_status = "IDLE"
updates_received = []

class RegisterNode(BaseModel):
    name: str

class WeightUpdate(BaseModel):
    node_id: str
    weights: List[Any]
    hash: str

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        nodes_count = db.query(db_models.Node).count()
        await manager.send_personal_message({
            "type": "initial_state",
            "stats": {
                "round": current_round_id,
                "total_blocks": len(blockchain.chain),
                "clients_active": nodes_count,
                "trust_score": 100.0,
                "status": round_status,
                "last_hash": blockchain.last_block.hash
            },
            "chain": blockchain.get_chain_dict()
        }, websocket)
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.post("/register")
async def register_node(node_data: RegisterNode, db: Session = Depends(get_db)):
    node_id = str(uuid.uuid4())[:8]
    new_node = db_models.Node(id=node_id, name=node_data.name)
    db.add(new_node)
    db.commit()
    await manager.broadcast({"type": "node_joined", "node_id": node_id, "name": node_data.name})
    return {"node_id": node_id}

@app.get("/download-model")
async def download_model():
    return {
        "round": current_round_id,
        "weights": ml_engine.get_serialized_global_weights()
    }

@app.post("/submit-update")
async def submit_update(data: WeightUpdate, db: Session = Depends(get_db)):
    global updates_received, round_status
    if round_status != "WAITING":
        raise HTTPException(status_code=400, detail="Not waiting for updates")
    
    node = db.query(db_models.Node).filter(db_models.Node.id == data.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if any(u["node_id"] == data.node_id for u in updates_received):
        return {"status": "ALREADY_SUBMITTED"}

    weights_np = [np.array(u) for u in data.weights]
    is_malicious = ml_engine.detect_malicious(weights_np)
    status = "REJECTED" if is_malicious else "ACCEPTED"
    
    await manager.broadcast({"type": "log", "data": {
        "client_id": data.node_id, "status": status, "timestamp": time.time(), "hash": data.hash[:16] + "..."
    }})
    
    if not is_malicious:
        updates_received.append({"node_id": data.node_id, "weights": weights_np})
        blockchain.add_new_transaction({"node_id": data.node_id, "round": current_round_id, "hash": data.hash, "status": "ACCEPTED"})
    
    db.add(db_models.Update(round_id=current_round_id, node_id=data.node_id, hash=data.hash, status=status))
    db.commit()
    return {"status": status}

@app.post("/initiate-round")
async def initiate_round(db: Session = Depends(get_db)):
    global current_round_id, round_status, updates_received
    if round_status != "IDLE":
        return {"status": "error", "message": f"Cannot initiate round in {round_status} state"}
    
    try:
        current_round_id += 1
        round_status = "WAITING"
        updates_received = []
        
        new_round = db_models.Round(id=current_round_id, status="WAITING")
        db.add(new_round)
        db.commit()
        
        await manager.broadcast({"type": "round_started", "round": current_round_id, "status": "WAITING"})
        return {"round": current_round_id}
    except Exception as e:
        db.rollback()
        round_status = "IDLE"
        current_round_id -= 1
        logger.error(f"Failed to initiate round: {e}")
        raise HTTPException(status_code=500, detail="Database error during initiation")

@app.post("/aggregate")
async def aggregate_round(db: Session = Depends(get_db)):
    global round_status, updates_received, current_round_id
    if round_status != "WAITING":
        raise HTTPException(status_code=400, detail="No round to aggregate")
    
    if not updates_received:
        round_status = "IDLE"
        await manager.broadcast({"type": "status_update", "status": "IDLE"})
        return {"status": "failed", "reason": "no_updates"}

    try:
        round_status = "AGGREGATING"
        await manager.broadcast({"type": "status_update", "status": "AGGREGATING"})
        
        # Simulating heavy aggregation work but ensuring status reset
        all_weights = [u["weights"] for u in updates_received]
        aggregated_weights = ml_engine.aggregate_updates(all_weights)
        ml_engine.update_global_model(aggregated_weights)
        
        blockchain.mine()
        
        round_db = db.query(db_models.Round).filter(db_models.Round.id == current_round_id).first()
        if round_db:
            round_db.status = "COMPLETED"
            round_db.end_time = datetime.datetime.utcnow()
            db.commit()
        
        round_status = "IDLE"
        updates_received = []
        await manager.broadcast({
            "type": "global_update",
            "stats": {
                "round": current_round_id,
                "total_blocks": len(blockchain.chain),
                "clients_active": db.query(db_models.Node).count(),
                "status": "IDLE",
                "last_hash": blockchain.last_block.hash
            },
            "chain": blockchain.get_chain_dict()
        })
        return {"status": "success"}
    except Exception as e:
        round_status = "IDLE" # Reset on failure
        await manager.broadcast({"type": "status_update", "status": "IDLE"})
        logger.error(f"Aggregation failed: {e}")
        raise HTTPException(status_code=500, detail="Aggregation failed")

@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    return {
        "round": current_round_id,
        "total_blocks": len(blockchain.chain),
        "clients_active": db.query(db_models.Node).count(),
        "status": round_status
    }

@app.get("/blockchain")
async def get_blockchain():
    return blockchain.get_chain_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
