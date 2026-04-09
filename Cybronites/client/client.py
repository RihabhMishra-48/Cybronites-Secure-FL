import flwr as fl
import torch
import numpy as np
import sys
import os
import logging
import urllib.request
from Cybronites.utils.structured_logging import setup_structured_logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GuardianClient")
setup_structured_logging("GuardianClient")

# Ensure project root and package directories are in path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check for root: either one level up (Cybronites root) or two levels up (Project root)
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))

for p in [current_dir, root_dir, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    # Try local submodule imports first (Most common in flattened deployment)
    from model import MNISTNet, train, test
    from dataset import load_data
    from security.privacy import apply_dp_to_updates, DPSpec
except ImportError:
    try:
        # Try package-prefixed imports (Common in local dev with Cybronites root)
        from client.model import MNISTNet, train, test
        from client.dataset import load_data
        from security.privacy import apply_dp_to_updates, DPSpec
    except ImportError:
        # Final fallback for legacy Cybronites structure
        from Cybronites.client.model import MNISTNet, train, test
        from Cybronites.client.dataset import load_data
        from security.privacy import apply_dp_to_updates, DPSpec

# Use CPU or GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class FlowerClient(fl.client.NumPyClient):
    """
    Secure Flower Client with Differential Privacy (DP) integration.
    """
    def __init__(self, client_id, train_loader, test_loader):
        self.client_id = client_id
        self.model = MNISTNet().to(device)
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.dp_spec = DPSpec(l2_norm_clip=1.0, noise_multiplier=0.01)
        self.local_cache = {} 
        self.ip_address = self._get_public_ip()

    def _get_public_ip(self):
        """Fetch node's public IP address for institutional auditing."""
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=2) as response:
                ip = response.read().decode('utf-8')
                logger.info(f"Client {self.client_id} | Public IP: {ip}")
                return ip
        except Exception:
            return "127.0.0.1"

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        """
        Local training with DP noise injection.
        """
        # Save initial parameters to compute the update (delta)
        initial_params = [torch.tensor(p).to(device) for p in parameters]
        self.set_parameters(parameters)
        
        optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01, momentum=0.9)
        logger.info(f"Client {self.client_id} | Training locally...", 
                    extra={"type": "training", "client_id": self.client_id, "status": "STARTED"})
        last_loss, last_acc = train(self.model, self.train_loader, optimizer, epochs=1, device=device)
        
        # Compute Parameter Update (Delta)
        new_params = [val.cpu() for _, val in self.model.state_dict().items()]
        updates_dict = {}
        for i, (name, param) in enumerate(self.model.state_dict().items()):
             updates_dict[name] = new_params[i] - initial_params[i].cpu()

        # Apply Differential Privacy
        logger.info(f"Client {self.client_id} | Applying DP Noise (ε-privacy)...", 
                    extra={"type": "privacy", "client_id": self.client_id, "dp_applied": True})
        dp_updates = apply_dp_to_updates(updates_dict, self.dp_spec)
        
        # Reconstruct final parameters: initial + dp_delta
        final_params = []
        for i, (name, _) in enumerate(self.model.state_dict().items()):
            param_with_noise = initial_params[i].cpu() + dp_updates[name]
            final_params.append(param_with_noise.numpy())

        return final_params, len(self.train_loader.dataset), {"accuracy": float(last_acc), "loss": float(last_loss), "ip": self.ip_address}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(self.model, self.test_loader, device=device)
        logger.info(f"Client {self.client_id} | Accuracy: {accuracy:.4f}", 
                    extra={"type": "evaluation", "client_id": self.client_id, "accuracy": accuracy})
        return float(loss), len(self.test_loader.dataset), {"accuracy": float(accuracy), "ip": self.ip_address}

def main():
    client_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    num_clients = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    logger.info(f"Starting Guardian Client {client_id}...")
    train_loader, test_loader = load_data(client_id=int(client_id), num_clients=num_clients)
    
    flower_port = int(os.environ.get("FLOWER_PORT", 8095))
    server_ip = os.environ.get("FL_SERVER_IP", "127.0.0.1")
    
    # Priority: Command Line Arg 3 > Env Var > Default
    if len(sys.argv) > 3:
        server_ip = sys.argv[3]
        
    server_address = f"{server_ip}:{flower_port}"
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to Secure Server at {server_address} (Attempt {attempt+1})...")
            fl.client.start_numpy_client(
                server_address=server_address,
                client=FlowerClient(client_id, train_loader, test_loader),
                grpc_max_message_length=512 * 1024 * 1024 # 512 MB
            )
            break
        except Exception as e:
            logger.warning(f"Connection failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)

if __name__ == "__main__":
    import time
    main()
