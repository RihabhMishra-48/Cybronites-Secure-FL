import os
import sys
import multiprocessing
import time
import logging
from typing import Optional, List

# Add root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from Cybronites.server.strategy import SecureFedAvg
from blockchain.ledger import Blockchain
from blockchain.reputation import ReputationManager

logger = logging.getLogger("Orchestrator")

def run_flower_server_proc(port, rounds, log_queue):
    """Isolated Process for Flower gRPC Server."""
    import flwr as fl
    import signal
    
    # Neutralize signals in sub-process
    signal.signal(signal.SIGINT, lambda sig, handler: None)
    
    # Log through tunnel
    log_queue.put(("LOG", f"[SERVER] INFO flwr | Flower gRPC Server is STARTING on port {port}"))
    
    ledger = Blockchain(difficulty=1)
    reputation = ReputationManager()

    # Pass the log_queue to the strategy
    strategy = SecureFedAvg(
        blockchain=ledger,
        reputation=reputation,
        min_fit_clients=2,
        min_available_clients=2,
        aggregation_method="median",
        log_queue=log_queue
    )

    try:
        fl.server.start_server(
            server_address=f"0.0.0.0:{port}",
            config=fl.server.ServerConfig(num_rounds=rounds),
            strategy=strategy,
            grpc_max_message_length=512 * 1024 * 1024
        )
    except Exception as e:
        log_queue.put(("LOG", f"[SERVER] ERROR: {e}"))

def run_simulation_client_proc(client_id, num_clients, port, log_queue):
    """Isolated Process for Federated Client."""
    import flwr as fl
    import torch
    import time
    from Cybronites.client.model import MNISTNet, train, test
    from Cybronites.client.dataset import load_data
    from security.privacy import apply_dp_to_updates, DPSpec
    
    log_queue.put(("LOG", f"[CLIENT {client_id}] INFO: Waiting for port {port}..."))
    time.sleep(5) # Wait for server bind
    
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        train_loader, test_loader = load_data(client_id=client_id, num_clients=num_clients)

        class InlineFlowerClient(fl.client.NumPyClient):
            def __init__(self, cid):
                self.cid = cid
                self.model = MNISTNet().to(device)
                self.dp_spec = DPSpec(l2_norm_clip=1.0, noise_multiplier=0.01)
                log_queue.put(("LOG", f"[CLIENT {self.cid}] INFO: gRPC channel opened."))

            def get_parameters(self, config):
                return [v.cpu().numpy() for v in self.model.state_dict().values()]

            def set_parameters(self, parameters):
                pairs = zip(self.model.state_dict().keys(), parameters)
                state = {k: torch.tensor(v) for k, v in pairs}
                self.model.load_state_dict(state, strict=True)

            def fit(self, parameters, config):
                log_queue.put(("LOG", f"[CLIENT {self.cid}] INFO: Training locally on MNIST..."))
                initial = [torch.tensor(p).to(device) for p in parameters]
                self.set_parameters(parameters)
                opt = torch.optim.SGD(self.model.parameters(), lr=0.01, momentum=0.9)
                last_loss, last_acc = train(self.model, train_loader, opt, epochs=1, device=device)
                
                log_queue.put(("LOG", f"[CLIENT {self.cid}] INFO: Applying DP Noise (ε-privacy)..."))
                new_params = [v.cpu() for v in self.model.state_dict().values()]
                updates = {name: new_params[i] - initial[i].cpu() for i, name in enumerate(self.model.state_dict().keys())}
                dp_updates = apply_dp_to_updates(updates, self.dp_spec)
                
                final = [(initial[i].cpu() + dp_updates[name]).numpy() for i, name in enumerate(self.model.state_dict().keys())]
                return final, len(train_loader.dataset), {"accuracy": float(last_acc), "loss": float(last_loss)}

            def evaluate(self, parameters, config):
                self.set_parameters(parameters)
                loss, acc = test(self.model, test_loader, device=device)
                log_queue.put(("LOG", f"[CLIENT {self.cid}] INFO: Local Accuracy: {acc:.4f}"))
                return float(loss), len(test_loader.dataset), {"accuracy": float(acc)}

        fl.client.start_numpy_client(
            server_address=f"127.0.0.1:{port}",
            client=InlineFlowerClient(client_id),
            grpc_max_message_length=512 * 1024 * 1024
        )
    except Exception as e:
        log_queue.put(("LOG", f"[CLIENT {client_id}] ERROR: {e}"))

class SimulationManager:
    _instance: Optional['SimulationManager'] = None
    _lock = multiprocessing.Lock()

    def __init__(self):
        self.server_proc: Optional[multiprocessing.Process] = None
        self.client_procs: List[multiprocessing.Process] = []
        self.is_running = multiprocessing.Value('b', False)
        self.flower_port = 8080
        self.log_queue = multiprocessing.Queue()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start_simulation(self, num_clients: int = 2):
        """Launches the entire stack using separate processes."""
        with self._lock:
            if self.is_running.value:
                return False, "Simulation already in progress."

            self.is_running.value = True
            
            # Start server process
            self.server_proc = multiprocessing.Process(
                target=run_flower_server_proc, 
                args=(self.flower_port, 100, self.log_queue),
                daemon=True
            )
            self.server_proc.start()

            # Start client processes
            self.client_procs = []
            for i in range(num_clients):
                p = multiprocessing.Process(
                    target=run_simulation_client_proc,
                    args=(i, num_clients, self.flower_port, self.log_queue),
                    daemon=True
                )
                p.start()
                self.client_procs.append(p)

            # Banner Broadcast (Sync from parent context via Bridge if possible)
            # Actually, the Banner will be sent via queue for consistency
            banner = [
                "============================================================",
                "  ALL SYSTEMS ONLINE (Institutional Cloud - Isolated)",
                "  Flow: Multi-Process Isolation Mode ACTIVE",
                f"  Clients:       {num_clients} Isolated Nodes",
                "  Stability:     Dashboard Event Loop Protected",
                "============================================================"
            ]
            for line in banner:
                self.log_queue.put(("LOG", line))

            return True, "Isolated Federated Training launched in sub-processes."

def get_orchestrator():
    return SimulationManager.get_instance()
