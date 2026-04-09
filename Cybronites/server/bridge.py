from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
import os
import time
import sqlite3
import urllib.request
from Cybronites.server.auth import router as auth_router
from Cybronites.utils.structured_logging import setup_structured_logging
import Cybronites.server.training_engine as engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("GuardianBridge")
setup_structured_logging("GuardianBridge")

class ConnectionManager:
    """Manages active WebSocket connections to the Institutional Dashboard."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None 
        self.state = {
            "round": 0,
            "total_blocks": 0,
            "clients_active": 0,
            "trust_avg": 0.0,
            "status": "IDLE",
            "last_hash": "N/A",
            "accuracy_history": [],
            "loss_history": [],
            "chain": [],
            "shards": [],
            "model_architecture": "# Loading Source Code...",
            "server_ip": "127.0.0.1" 
        }
        self.log_buffer: List[str] = []
        self.cache = {
            "last_sync": 0,
            "round_snapshots": {}, # Cache for historical round data
            "blockchain_cache": []
        }

    def load_model_code(self):
        """Reads model.py and injects it into local state."""
        try:
            # Check multiple potential locations (local vs deployed)
            paths = [
                os.path.join(os.getcwd(), "Cybronites", "client", "model.py"),
                os.path.join(os.getcwd(), "client", "model.py"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client", "model.py")
            ]
            for model_path in paths:
                if os.path.exists(model_path):
                    with open(model_path, "r") as f:
                        self.state["model_architecture"] = f.read()
                        logger.info(f"Model source code loaded from {model_path}")
                        return
        except Exception as e:
            logger.error(f"Failed to load model source: {e}")

    def fetch_public_ip(self):
        """Fetches the external IP address (for Hugging Face deployment visualization)."""
        try:
            # Use public IP discovery service
            with urllib.request.urlopen("https://api.ipify.org", timeout=2) as response:
                ip = response.read().decode('utf-8')
                self.state["server_ip"] = ip
                logger.info(f"Public IP fetched: {ip}")
        except Exception as e:
            logger.warning(f"Could not fetch public IP (offline/firewalled): {e}")
            # Fallback to local
            self.state["server_ip"] = "127.0.0.1"
    def load_db_shards(self):
        """Fetches real institutional shards from guardian.db."""
        try:
            paths = [
                os.path.join(os.getcwd(), "Cybronites", "guardian.db"),
                os.path.join(os.getcwd(), "guardian.db")
            ]
            db_path = None
            for p in paths:
                if os.path.exists(p):
                    db_path = p
                    break
            
            if not db_path:
                return
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM shards")
            rows = [dict(row) for row in cur.fetchall()]
            self.state["shards"] = rows
            conn.close()
            logger.info(f"Loaded {len(rows)} shards from {db_path}")
        except Exception as e:
            logger.error(f"DB Shard Load Error: {e}")

    def save_node_to_db(self, node_id, ip, trust_score):
        """Persist node metadata to the institutional record."""
        try:
            paths = [
                os.path.join(os.getcwd(), "Cybronites", "guardian.db"),
                os.path.join(os.getcwd(), "guardian.db")
            ]
            db_path = None
            for p in paths:
                if os.path.exists(p):
                    db_path = p
                    break
            
            if not db_path: return

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # Upsert logic (insert or update on id)
            cur.execute("""
                INSERT INTO nodes (id, name, last_seen, trust_score, ip_address) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET 
                    last_seen=excluded.last_seen,
                    trust_score=excluded.trust_score,
                    ip_address=excluded.ip_address
            """, (node_id, f"Node_{node_id[:4]}", time.strftime('%Y-%m-%d %H:%M:%S'), trust_score, ip))
            
            conn.commit()
            conn.close()
            logger.info(f"Node {node_id} persisted to database with IP {ip}.")
        except Exception as e:
            logger.warning(f"Database Persistence Failed for node {node_id}: {e}")

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            if self.loop is None:
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
            
            # Fresh read of the model code and DB shards
            self.load_model_code()
            self.load_db_shards()
                
            # Send initial state snapshot
            await self.send_json({
                "type": "INITIAL_SYNC",
                "payload": {
                    "state": self.state,
                    "logs": self.log_buffer[-20:] # Last 20 logs
                }
            }, websocket)
            logger.info(f"Dashboard connected. Total subscribers: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Dashboard disconnected. Remaining: {len(self.active_connections)}")

    async def send_json(self, data: dict, websocket: WebSocket):
        """Defensive JSON delivery."""
        try:
            # Only send if the websocket is actively connected
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_json(data)
        except Exception as e:
            logger.error(f"WS Serialization/Send Error: {e}")
            self.disconnect(websocket)

    def broadcast_sync(self, message_type: str, payload: Any):
        """Thread-safe synchronous broadcast for use from Flower threads."""
        if self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(message_type, payload), 
                    self.loop
                )
            except Exception as e:
                logger.warning(f"Thread-safe broadcast failed: {e}")
        else:
            # Fallback for early startup: just buffer it
            if message_type == "LOG":
                self.log_buffer.append(payload)
                if len(self.log_buffer) > 200: self.log_buffer.pop(0)
            logger.debug(f"Broadcast deferred (loop not ready): {message_type}")

    async def broadcast(self, message_type: str, payload: Any):
        """Reactive broadcast engine."""
        if message_type == "STAT_UPDATE":
            # 1. Update local state
            self.state.update(payload)
            
            # 2. Update Cache for responsiveness
            if "round" in payload:
                r = payload["round"]
                self.cache["round_snapshots"][r] = payload
            
            if "chain" in payload:
                self.cache["blockchain_cache"] = payload["chain"]
            
            self.cache["last_sync"] = time.time()
            
            # Diagnostic for history persistence
            if "accuracy_history" in payload:
                hist_size = len(payload["accuracy_history"])
                logger.info(f"Broadcasting STAT_UPDATE. Accuracy History Size: {hist_size}", 
                            extra={"type": "telemetry", "round": payload.get("round"), "history_size": hist_size})
            
        elif message_type == "LOG":
            self.log_buffer.append(payload)
            if len(self.log_buffer) > 200: self.log_buffer.pop(0)

        # Create output packet
        data = {"type": message_type, "payload": payload}
        
        # Dispatch to all active dashboards
        if self.active_connections:
            for connection in self.active_connections:
                await self.send_json(data, connection)

# Singleton instance
bridge = ConnectionManager()
app = FastAPI(title="AI Guardian Bridge")

# Mandatory middleware initialization BEFORE including routers for consistent CORS headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth Routes after middleware
app.include_router(auth_router)

@app.on_event("startup")
async def startup():
    bridge.loop = asyncio.get_running_loop()
    bridge.load_model_code()
    bridge.fetch_public_ip()
    
    # Initialize Orchestrator and start Log Listener thread
    from Cybronites.server.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    
    def log_listener_worker():
        """Background thread to pipe logs from multiprocessing.Queue to bridge.broadcast_sync."""
        logger.info("IPC Log Listener thread started.")
        while True:
            try:
                # Blocking read from queue
                message_type, payload = orchestrator.log_queue.get()
                bridge.broadcast_sync(message_type, payload)
            except Exception as e:
                logger.error(f"IPC Log Tunnel Error: {e}")
                time.sleep(1)

    import threading
    threading.Thread(target=log_listener_worker, daemon=True).start()
    
    logger.info("Guardian Bridge Event Loop context captured.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await bridge.connect(websocket)
    try:
        while True:
            # Keep-alive loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        bridge.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Runtime Error: {e}")
        bridge.disconnect(websocket)

@app.get("/api/health")
@app.get("/status")
async def health_check():
    return {"status": "ONLINE", "clients": len(bridge.active_connections)}

@app.post("/api/v1/federated/start")
async def start_federated_training():
    """Triggers a new federated training session using in-process threads.
    Uses the same pattern as the working app.py auto-start."""
    import threading
    import flwr as fl
    
    FLOWER_PORT = 8080
    _flower_ready = threading.Event()
    
    def _run_server():
        """Background thread for Flower gRPC server."""
        import signal
        from Cybronites.server.strategy import SecureFedAvg
        from blockchain.ledger import Blockchain
        from blockchain.reputation import ReputationManager
        
        original_signal = signal.signal
        signal.signal = lambda *a, **kw: None  # Neutralize in non-main thread
        
        ledger = Blockchain(difficulty=1)
        reputation = ReputationManager()
        strategy = SecureFedAvg(
            blockchain=ledger,
            reputation=reputation,
            min_fit_clients=2,
            min_available_clients=2,
            aggregation_method="median",
        )
        _flower_ready.set()
        try:
            fl.server.start_server(
                server_address=f"0.0.0.0:{FLOWER_PORT}",
                config=fl.server.ServerConfig(num_rounds=5),
                strategy=strategy,
                grpc_max_message_length=512 * 1024 * 1024,
            )
        except Exception as e:
            logger.error(f"Flower Server error: {e}")
        finally:
            signal.signal = original_signal
    
    def _run_client(cid, num_clients=2):
        """Background thread for a simulation client."""
        _flower_ready.wait(timeout=60)
        import time as _t; _t.sleep(5)
        try:
            from Cybronites.client.model import MNISTNet, train as _train, test as _test
            from Cybronites.client.dataset import load_data
            from security.privacy import apply_dp_to_updates, DPSpec
            import torch
            import urllib.request
            
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            try:
                with urllib.request.urlopen("https://api.ipify.org", timeout=2) as r:
                    ip = r.read().decode("utf-8")
            except Exception:
                ip = "127.0.0.1"
            
            train_loader, test_loader = load_data(client_id=cid, num_clients=num_clients)
            
            class _Client(fl.client.NumPyClient):
                def __init__(self):
                    self.model = MNISTNet().to(device)
                    self.dp_spec = DPSpec(l2_norm_clip=1.0, noise_multiplier=0.01)
                def get_parameters(self, config):
                    return [v.cpu().numpy() for v in self.model.state_dict().values()]
                def set_parameters(self, parameters):
                    pairs = zip(self.model.state_dict().keys(), parameters)
                    self.model.load_state_dict({k: torch.tensor(v) for k, v in pairs}, strict=True)
                def fit(self, parameters, config):
                    initial = [torch.tensor(p).to(device) for p in parameters]
                    self.set_parameters(parameters)
                    opt = torch.optim.SGD(self.model.parameters(), lr=0.01, momentum=0.9)
                    loss, acc = _train(self.model, train_loader, opt, epochs=1, device=device)
                    new_params = [v.cpu() for v in self.model.state_dict().values()]
                    updates = {n: new_params[i] - initial[i].cpu() for i, (n, _) in enumerate(self.model.state_dict().items())}
                    dp = apply_dp_to_updates(updates, self.dp_spec)
                    final = [(initial[i].cpu() + dp[n]).numpy() for i, (n, _) in enumerate(self.model.state_dict().items())]
                    return final, len(train_loader.dataset), {"accuracy": float(acc), "loss": float(loss), "ip": ip}
                def evaluate(self, parameters, config):
                    self.set_parameters(parameters)
                    loss, acc = _test(self.model, test_loader, device=device)
                    return float(loss), len(test_loader.dataset), {"accuracy": float(acc), "ip": ip}
            
            fl.client.start_numpy_client(
                server_address=f"127.0.0.1:{FLOWER_PORT}",
                client=_Client(),
                grpc_max_message_length=512 * 1024 * 1024,
            )
        except Exception as e:
            logger.error(f"Client {cid} error: {e}")
    
    # Launch server + clients as threads (same process = shared bridge)
    threading.Thread(target=_run_server, daemon=True).start()
    for cid in range(2):
        threading.Thread(target=_run_client, args=(cid, 2), daemon=True).start()
        import time as _t; _t.sleep(1)
    
    await bridge.broadcast("LOG", "SYSTEM: Federated Training session launched.")
    return {"success": True, "message": "Federated Training launched."}

@app.post("/api/v1/laboratory/validate")
async def validate_code(data: Dict[str, str]):
    code = data.get("code", "")
    try:
        if not code.strip():
            return {"success": False, "error": "Empty source code submitted."}
            
        # 1. Syntactic analysis
        import ast
        ast.parse(code)
        
        # 2. Compilation check (Catching PyTorch import context errors)
        compile(code, '<laboratory>', 'exec')
        
        return {"success": True}
    except SyntaxError as e:
        # Professional Diagnostic Extraction
        return {
            "success": False, 
            "error": str(e.msg), 
            "line": e.lineno, 
            "column": e.offset,
            "type": "SyntaxError"
        }
    except Exception as e:
        import traceback
        logger.error(f"Laboratory Validation Error: {e}")
        return {"success": False, "error": str(e), "type": type(e).__name__}

@app.post("/api/v1/laboratory/deploy")
async def deploy_model(data: Dict[str, str]):
    code = data.get("code", "")
    try:
        # Verify before writing to prevent system crashes
        import ast
        ast.parse(code)
        
        # Target local Cybronites environment
        target_path = os.path.join(os.getcwd(), "Cybronites", "client", "model.py")
        
        # Fallback for relative server context
        if not os.path.exists(os.path.dirname(target_path)):
            target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client", "model.py")
            
        with open(target_path, "w") as f:
            f.write(code)
            
        logger.info(f"Local Dynamic Model HOT-SWAPPED at {target_path}")
        
        # Synchronize live state
        bridge.state["model_architecture"] = code
        await bridge.broadcast("LOG", "SYSTEM: Local model hot-swapped. Synchronizing nodes...")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Local Deployment Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/v1/laboratory/train")
async def start_lab_training(data: Dict[str, Any]):
    code = data.get("code", "")
    hyperparams = data.get("hyperparams", {})
    
    if not code:
        return {"success": False, "error": "No code provided."}
    
    success, msg = engine.start_training(code, hyperparams, bridge.broadcast_sync)
    return {"success": success, "message": msg}

@app.post("/api/v1/laboratory/abort")
async def abort_lab_training():
    success = engine.abort_training()
    return {"success": success}

@app.get("/api/v1/laboratory/status")
async def get_lab_status():
    return engine.get_session_status()

@app.get("/api/v1/laboratory/download/{file_format}")
async def download_model(file_format: str):
    session = engine._current_session
    if not session or not session.model_path:
        return {"error": "No model available for download."}
    
    if file_format == "pt":
        path = session.model_path
        filename = "model_weights.pt"
    elif file_format == "onnx":
        path = session.model_path.replace(".pt", ".onnx")
        filename = "model_weights.onnx"
    else:
        return {"error": "Invalid format. Use 'pt' or 'onnx'."}
        
    if not os.path.exists(path):
        return {"error": f"File {filename} not found."}
        
    return FileResponse(path, filename=filename)

# ── Static Dashboard Serving (for Deployment) ──
# Look for 'static' (Hugging Face) or 'dist' (Local build)
paths_to_check = [
    os.path.join(os.getcwd(), "static"),
    os.path.join(os.getcwd(), "dist"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dist")
]

for s_dir in paths_to_check:
    if os.path.exists(s_dir) and os.path.isdir(s_dir):
        assets_dir = os.path.join(s_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_dashboard(full_path: str):
            # Block internal API/WS from being caught by static server
            if full_path.startswith("api") or full_path.startswith("ws"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)
            # Try to serve index.html from whichever static dir we found
            return FileResponse(os.path.join(s_dir, "index.html"))
        logger.info(f"Serving dashboard from {s_dir}")
        break

def start_bridge(port: int = 7860):
    import uvicorn
    logger.info(f"Launching Guardian Bridge on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
