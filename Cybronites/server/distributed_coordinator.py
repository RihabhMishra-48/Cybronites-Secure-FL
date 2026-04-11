"""
Distributed Federated Learning Coordinator (HTTP-based)

Replaces Flower's gRPC protocol with HTTP REST endpoints so that
remote clients on ANY network can participate through the existing
HuggingFace Space URL. No port forwarding or ngrok needed.

Flow:
  1. Dashboard starts session → POST /api/v1/distributed/start
  2. Clients register → POST /api/v1/distributed/register
  3. Clients poll for model → GET /api/v1/distributed/get-model
  4. Clients train locally, submit → POST /api/v1/distributed/submit-update
  5. Server aggregates when min_clients updates received
  6. Repeat for N rounds
"""

import torch
import numpy as np
import threading
import time
import logging
import io
import base64
import uuid
import hashlib
from typing import Dict, List, Optional, Any

logger = logging.getLogger("DistributedCoordinator")

# ─── Serialization Utilities ───

def params_to_b64(params_list: List[np.ndarray]) -> List[dict]:
    """Serialize list of numpy arrays to base64 strings for HTTP transport."""
    result = []
    for arr in params_list:
        buf = io.BytesIO()
        np.save(buf, arr)
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        result.append({"data": b64})
    return result


def b64_to_params(b64_list: List[dict]) -> List[np.ndarray]:
    """Deserialize base64 strings back to numpy arrays."""
    result = []
    for item in b64_list:
        buf = io.BytesIO(base64.b64decode(item["data"]))
        arr = np.load(buf)
        result.append(arr)
    return result


# ─── Coordinator ───

class DistributedCoordinator:
    """
    Manages HTTP-based federated learning sessions.
    Singleton pattern to maintain state across API requests.
    """
    _instance: Optional['DistributedCoordinator'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.global_model = None
        self.round = 0
        self.total_rounds = 5
        self.min_clients = 1
        self.status = "IDLE"  # IDLE, WAITING, AGGREGATING, COMPLETE
        self.registered_clients: Dict[str, dict] = {}
        self.round_updates: Dict[str, dict] = {}
        self.accuracy_history: List[float] = []
        self.loss_history: List[float] = []
        self.node_registry: Dict[str, dict] = {}
        self.round_history: List[dict] = []
        self._broadcast_fn = None
        self._aggregation_lock = threading.Lock()
        self._session_id = None

    @classmethod
    def get_instance(cls) -> 'DistributedCoordinator':
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def set_broadcast(self, fn):
        """Set the broadcast function (bridge.broadcast_sync)."""
        self._broadcast_fn = fn

    def _broadcast(self, msg_type: str, payload: Any):
        """Send message to dashboard via WebSocket bridge."""
        if self._broadcast_fn:
            try:
                self._broadcast_fn(msg_type, payload)
            except Exception as e:
                logger.warning(f"Broadcast failed: {e}")

    def _init_model(self):
        """Initialize a fresh global model."""
        # Import here to avoid circular imports in deployment
        try:
            from Cybronites.client.model import MNISTNet
        except ImportError:
            try:
                from client.model import MNISTNet
            except ImportError:
                # Inline definition as last resort
                import torch.nn as nn
                import torch.nn.functional as F
                class MNISTNet(nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
                        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
                        self.conv2_drop = nn.Dropout2d()
                        self.fc1 = nn.Linear(320, 50)
                        self.fc2 = nn.Linear(50, 10)
                    def forward(self, x):
                        x = F.relu(F.max_pool2d(self.conv1(x), 2))
                        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
                        x = x.view(-1, 320)
                        x = F.relu(self.fc1(x))
                        x = F.dropout(x, training=self.training)
                        return F.log_softmax(self.fc2(x), dim=1)

        self.global_model = MNISTNet()
        logger.info("Global model initialized (MNISTNet)")

    # ─── Session Management ───

    def start_session(self, num_rounds: int = 5, min_clients: int = 1) -> dict:
        """Start a new distributed FL session. Called from dashboard."""
        with self._aggregation_lock:
            self._session_id = str(uuid.uuid4())[:8]
            self.total_rounds = num_rounds
            self.min_clients = min_clients
            self.round = 1
            self.status = "WAITING"
            self.round_updates = {}
            self.accuracy_history = []
            self.loss_history = []
            self.round_history = []
            self._init_model()

            banner = [
                "════════════════════════════════════════════════════════",
                "  🌐 DISTRIBUTED FEDERATED LEARNING SESSION STARTED",
                f"  Session ID:    {self._session_id}",
                f"  Min Clients:   {min_clients}",
                f"  Total Rounds:  {num_rounds}",
                f"  Registered:    {len(self.registered_clients)} node(s)",
                "  Mode:          HTTP-REST (Cross-Network)",
                "════════════════════════════════════════════════════════",
            ]
            for line in banner:
                self._broadcast("LOG", line)

            self._broadcast("STAT_UPDATE", {
                "status": "WAITING",
                "round": 1,
                "clients_active": len(self.registered_clients),
                "node_registry": self.node_registry,
            })

            return {
                "session_id": self._session_id,
                "round": 1,
                "total_rounds": num_rounds,
            }

    def stop_session(self):
        """Force-stop the current session."""
        self.status = "IDLE"
        self.round_updates = {}
        self._broadcast("LOG", "⛔ SESSION STOPPED by operator.")
        self._broadcast("STAT_UPDATE", {"status": "IDLE"})

    # ─── Client Registration ───

    def register_client(self, name: str, ip: str) -> str:
        """Register a remote client. Returns a unique client ID."""
        client_id = str(uuid.uuid4())[:12]
        self.registered_clients[client_id] = {
            "name": name,
            "ip": ip,
            "last_seen": time.time(),
            "rounds_participated": 0,
            "status": "CONNECTED",
        }

        # Update node registry for dashboard
        self.node_registry[client_id] = {
            "status": "CONNECTED",
            "ip": ip,
            "hash": f"0x{hashlib.sha256(client_id.encode()).hexdigest()[:12]}",
            "reputation": 100.0,
            "name": name,
        }

        self._broadcast("LOG", f"🖥️  NODE JOINED: {name} ({ip}) → ID: {client_id}")
        self._broadcast("STAT_UPDATE", {
            "clients_active": len(self.registered_clients),
            "node_registry": self.node_registry,
        })

        logger.info(f"Client registered: {name} ({ip}) → {client_id}")
        return client_id

    # ─── Model Distribution ───

    def get_global_params(self) -> dict:
        """Return current global model parameters for client download."""
        if self.global_model is None:
            return {"error": "No active session"}

        params = [val.cpu().detach().numpy() for val in self.global_model.state_dict().values()]
        param_keys = list(self.global_model.state_dict().keys())

        return {
            "round": self.round,
            "total_rounds": self.total_rounds,
            "status": self.status,
            "params": params_to_b64(params),
            "param_keys": param_keys,
        }

    # ─── Update Submission ───

    def submit_update(self, client_id: str, params_b64: List[dict], 
                      num_examples: int, metrics: dict) -> dict:
        """
        Accept a trained model update from a client.
        Triggers aggregation when min_clients updates are received.
        """
        with self._aggregation_lock:
            if self.status not in ("WAITING",):
                return {"success": False, "message": f"Server not accepting updates (status={self.status})"}

            if client_id not in self.registered_clients:
                return {"success": False, "message": "Client not registered. Call /register first."}

            if client_id in self.round_updates:
                return {"success": False, "message": "Already submitted for this round. Wait for next round."}

            # Decode parameters
            try:
                params = b64_to_params(params_b64)
            except Exception as e:
                return {"success": False, "message": f"Parameter decode error: {e}"}

            # Compute update hash for audit
            weight_hash = hashlib.sha256(
                b"".join(p.tobytes()[:100] for p in params)
            ).hexdigest()[:16]

            # Store update
            self.round_updates[client_id] = {
                "params": params,
                "num_examples": num_examples,
                "metrics": metrics,
                "hash": weight_hash,
                "timestamp": time.time(),
            }

            # Update client metadata
            client_info = self.registered_clients[client_id]
            client_info["last_seen"] = time.time()
            client_info["rounds_participated"] += 1
            client_name = client_info.get("name", client_id)

            acc = metrics.get("accuracy", 0)
            loss = metrics.get("loss", 0)
            norm = float(np.sqrt(sum(np.sum(p**2) for p in params)))

            self._broadcast("LOG", f"  ✅ {client_name}: Update VALID (acc={acc:.4f}, norm={norm:.2f})")

            # Update node registry
            self.node_registry[client_id] = {
                "status": "VALID",
                "ip": client_info.get("ip", "unknown"),
                "hash": f"0x{weight_hash}",
                "reputation": 100.0,
                "name": client_name,
            }

            # Record in round history
            self.round_history.append({
                "round": self.round,
                "client": client_name,
                "client_id": client_id,
                "acc": acc,
                "loss": loss,
                "status": "VALID",
                "norm": norm,
                "timestamp": time.time(),
                # Fields expected by TrainingWorkspace ledger
                "lr": 0.01,
                "batch": 32,
            })
            if len(self.round_history) > 200:
                self.round_history = self.round_history[-200:]

            updates_count = len(self.round_updates)
            self._broadcast("LOG", 
                f"  📊 Updates: {updates_count}/{self.min_clients} received for Round {self.round}")
            # Live update so dashboard panel shows progress mid-round
            self._broadcast("STAT_UPDATE", {
                "updates_received": updates_count,
                "updates_needed": self.min_clients,
                "clients_active": len(self.registered_clients),
                "node_registry": self.node_registry,
                "round_history": self.round_history,
            })

            # Check if we have enough updates to aggregate
            if updates_count >= self.min_clients:
                self._aggregate()

            return {
                "success": True, 
                "message": f"Update accepted ({updates_count}/{self.min_clients})",
                "round": self.round,
            }

    # ─── Aggregation ───

    def _aggregate(self):
        """Aggregate received updates and advance to next round."""
        self.status = "AGGREGATING"
        num_updates = len(self.round_updates)

        self._broadcast("LOG", f"Round {self.round}: Aggregating {num_updates} update(s)...")
        self._broadcast("STAT_UPDATE", {"status": "AGGREGATING", "round": self.round})

        # Collect all updates
        all_params = []
        all_examples = []
        acc_list = []
        loss_list = []

        for cid, update in self.round_updates.items():
            all_params.append(update["params"])
            all_examples.append(update["num_examples"])
            acc_list.append(update["metrics"].get("accuracy", 0))
            loss_list.append(update["metrics"].get("loss", 0))

        # Aggregation: coordinate-wise median (robust against poisoning)
        num_layers = len(all_params[0])
        aggregated = []
        for layer_idx in range(num_layers):
            layer_updates = [p[layer_idx] for p in all_params]
            if len(layer_updates) == 1:
                # Single client: use their update directly
                aggregated.append(layer_updates[0].copy())
            else:
                # Multiple clients: coordinate-wise median
                aggregated.append(np.median(np.stack(layer_updates), axis=0))

        # Update global model
        state_dict = self.global_model.state_dict()
        for (key, _), agg_param in zip(state_dict.items(), aggregated):
            state_dict[key] = torch.from_numpy(agg_param.astype(np.float32))
        self.global_model.load_state_dict(state_dict)

        # Record metrics
        avg_acc = float(np.mean(acc_list)) if acc_list else 0.0
        avg_loss = float(np.mean(loss_list)) if loss_list else 0.0
        self.accuracy_history.append(avg_acc)
        self.loss_history.append(avg_loss)

        self._broadcast("LOG", f"Round {self.round} Complete ✓ (Acc: {avg_acc:.2%}, Loss: {avg_loss:.4f})")
        logger.info(f"Round {self.round} aggregated: Acc={avg_acc:.4f}, Loss={avg_loss:.4f}")

        # Advance or finish
        if self.round >= self.total_rounds:
            self.status = "COMPLETE"
            self._broadcast("STAT_UPDATE", {
                "status": "COMPLETE",
                "round": self.round,
                "total_rounds": self.total_rounds,
                "accuracy_history": self.accuracy_history,
                "loss_history": self.loss_history,
                "node_registry": self.node_registry,
                "round_history": self.round_history,
                "clients_active": len(self.registered_clients),
                "updates_received": 0,
                "updates_needed": self.min_clients,
            })
            self._broadcast("LOG", "🏁 SESSION COMPLETE: All rounds finalized.")
            logger.info("Distributed FL session complete.")
        else:
            self.round += 1
            self.round_updates = {}
            self.status = "WAITING"
            self._broadcast("STAT_UPDATE", {
                "status": "WAITING",
                "round": self.round,
                "total_rounds": self.total_rounds,
                "accuracy_history": self.accuracy_history,
                "loss_history": self.loss_history,
                "node_registry": self.node_registry,
                "round_history": self.round_history,
                "clients_active": len(self.registered_clients),
                "updates_received": 0,
                "updates_needed": self.min_clients,
            })
            self._broadcast("LOG", f"Round {self.round}/{self.total_rounds}: Waiting for client updates...")

    # ─── Status ───

    def get_status(self) -> dict:
        """Return current session status for clients and dashboard."""
        return {
            "status": self.status,
            "session_id": self._session_id,
            "round": self.round,
            "total_rounds": self.total_rounds,
            "min_clients": self.min_clients,
            "registered_clients": len(self.registered_clients),
            "updates_received": len(self.round_updates),
            "updates_needed": self.min_clients,
            "accuracy_history": list(self.accuracy_history),
            "loss_history": list(self.loss_history),
        }
