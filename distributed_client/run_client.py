#!/usr/bin/env python3
"""
Cybronites — Distributed Learning Client

Run this on ANY device to participate in federated training.
No special setup needed — just Python + PyTorch.

Usage:
    python run_client.py --server https://rishuuuuuu-cybronites-secure-fl.hf.space --name "My-Laptop"
"""

import argparse
import requests
import time
import sys
import os
import io
import base64
import logging
import urllib.request

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)-7s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CybronitesClient")


# ════════════════════════════════════════════════════════════
#  MODEL — Must match the server's architecture exactly
# ════════════════════════════════════════════════════════════

class MNISTNet(nn.Module):
    """Lightweight CNN for MNIST digit classification."""
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


# ════════════════════════════════════════════════════════════
#  DATA LOADING
# ════════════════════════════════════════════════════════════

def load_mnist(batch_size=32):
    """Download and prepare MNIST dataset."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    train = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test = datasets.MNIST(data_dir, train=False, download=True, transform=transform)
    
    train_loader = DataLoader(train, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test, batch_size=1000, shuffle=False)
    
    return train_loader, test_loader


# ════════════════════════════════════════════════════════════
#  LOCAL TRAINING
# ════════════════════════════════════════════════════════════

def train_local(model, train_loader, device, epochs=1):
    """Train the model locally on this device's data."""
    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    last_loss = 0.0
    correct = 0
    total = 0
    
    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = F.nll_loss(output, target)
            loss.backward()
            optimizer.step()
            
            last_loss = loss.item()
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += len(target)
    
    accuracy = correct / total if total else 0
    return last_loss, accuracy


def evaluate(model, test_loader, device):
    """Evaluate model on test set."""
    model.eval()
    correct = 0
    total = 0
    test_loss = 0
    
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += len(target)
    
    accuracy = correct / total if total else 0
    avg_loss = test_loss / total if total else 0
    return avg_loss, accuracy


# ════════════════════════════════════════════════════════════
#  WEIGHT SERIALIZATION (numpy → base64 for HTTP transport)
# ════════════════════════════════════════════════════════════

def model_to_b64(model):
    """Serialize all model parameters to base64 for HTTP upload."""
    result = []
    for val in model.state_dict().values():
        arr = val.cpu().detach().numpy()
        buf = io.BytesIO()
        np.save(buf, arr)
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        result.append({"data": b64})
    return result


def b64_to_model(model, b64_list):
    """Load base64-serialized parameters into the model."""
    params = []
    for item in b64_list:
        buf = io.BytesIO(base64.b64decode(item["data"]))
        arr = np.load(buf)
        params.append(arr)
    
    state_dict = model.state_dict()
    for (key, _), param in zip(state_dict.items(), params):
        state_dict[key] = torch.from_numpy(param)
    model.load_state_dict(state_dict)


# ════════════════════════════════════════════════════════════
#  NETWORK UTILITIES
# ════════════════════════════════════════════════════════════

def get_public_ip():
    """Detect this device's public IP for identification."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=3) as r:
            return r.read().decode('utf-8')
    except Exception:
        return "unknown"


def api_call(method, url, json=None, retries=3, timeout=120):
    """Resilient API call with retries."""
    for attempt in range(retries):
        try:
            if method == "GET":
                resp = requests.get(url, timeout=timeout)
            else:
                resp = requests.post(url, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.ConnectionError:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                logger.warning(f"Connection failed. Retrying in {wait}s... ({attempt+1}/{retries})")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"Request error: {e}. Retrying...")
                time.sleep(3)
            else:
                raise


# ════════════════════════════════════════════════════════════
#  MAIN CLIENT LOOP
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Cybronites Distributed Learning Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_client.py --server https://rishuuuuuu-cybronites-secure-fl.hf.space --name "Lab-PC"
  python run_client.py --server http://192.168.1.100:7860 --name "Rishu-Laptop" --epochs 2
        """
    )
    parser.add_argument("--server", required=True, 
                        help="Server URL (e.g., https://your-space.hf.space)")
    parser.add_argument("--name", default="Client-Node", 
                        help="Display name for this device")
    parser.add_argument("--epochs", type=int, default=1, 
                        help="Local training epochs per round")
    parser.add_argument("--batch-size", type=int, default=32, 
                        help="Training batch size")
    args = parser.parse_args()

    server = args.server.rstrip("/")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    my_ip = get_public_ip()

    # ─── Banner ───
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║       🛡️  CYBRONITES DISTRIBUTED LEARNING CLIENT         ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Server  : {server:<44s}║
    ║  Device  : {str(device):<44s}║
    ║  Name    : {args.name:<44s}║
    ║  IP      : {my_ip:<44s}║
    ║  Epochs  : {str(args.epochs):<44s}║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # ─── Step 1: Health Check ───
    logger.info("Checking server connectivity...")
    try:
        health = api_call("GET", f"{server}/api/health")
        logger.info(f"Server ONLINE ✓ (Active connections: {health.get('clients', 0)})")
    except Exception as e:
        logger.error(f"Cannot reach server at {server}: {e}")
        logger.error("Make sure the server URL is correct and accessible.")
        sys.exit(1)

    # ─── Step 2: Register ───
    logger.info("Registering with server...")
    try:
        reg = api_call("POST", f"{server}/api/v1/distributed/register", 
                       json={"name": args.name, "ip": my_ip})
        
        if not reg.get("success"):
            logger.error(f"Registration failed: {reg}")
            sys.exit(1)
        
        client_id = reg["client_id"]
        logger.info(f"✅ Registered! Client ID: {client_id}")
        logger.info(f"   Session Status: {reg.get('session_status', 'unknown')}")
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        sys.exit(1)

    # ─── Step 3: Load Data ───
    logger.info("Loading MNIST dataset (downloading if needed)...")
    train_loader, test_loader = load_mnist(batch_size=args.batch_size)
    logger.info(f"Dataset ready: {len(train_loader.dataset)} training, {len(test_loader.dataset)} test samples")
    
    model = MNISTNet().to(device)
    last_completed_round = 0

    # ─── Step 4: Training Loop ───
    logger.info("Entering training loop... (Ctrl+C to stop)\n")
    
    while True:
        try:
            # Poll server status
            status = api_call("GET", f"{server}/api/v1/distributed/status")
            
            current_status = status.get("status", "IDLE")
            current_round = status.get("round", 0)
            total_rounds = status.get("total_rounds", 0)

            # ── IDLE: No session running ──
            if current_status == "IDLE":
                sys.stdout.write(f"\r⏳ Waiting for training session to start... (registered as '{args.name}')")
                sys.stdout.flush()
                time.sleep(3)
                continue

            # ── COMPLETE: Session finished ──
            if current_status == "COMPLETE":
                print()
                logger.info("🏁 Training session COMPLETE!")
                acc_hist = status.get("accuracy_history", [])
                if acc_hist:
                    logger.info(f"   Final Accuracy: {acc_hist[-1]:.2%}")
                    logger.info(f"   Accuracy Progression: {[f'{a:.2%}' for a in acc_hist]}")
                
                # Wait for a new session
                logger.info("Waiting for a new session...")
                last_completed_round = 0
                time.sleep(5)
                continue

            # ── AGGREGATING: Server is processing ──
            if current_status == "AGGREGATING":
                sys.stdout.write(f"\r⚙️  Round {current_round}: Server aggregating... waiting...")
                sys.stdout.flush()
                time.sleep(2)
                continue

            # ── WAITING: Server needs our update ──
            if current_status == "WAITING" and current_round > last_completed_round:
                print()  # Newline after status dots
                logger.info(f"{'═'*55}")
                logger.info(f"  ROUND {current_round}/{total_rounds}")
                logger.info(f"{'═'*55}")

                # Download global model
                logger.info("📥 Downloading global model from server...")
                model_data = api_call("GET", f"{server}/api/v1/distributed/get-model")

                if "error" in model_data:
                    logger.warning(f"Server: {model_data['error']}")
                    time.sleep(3)
                    continue

                if "params" in model_data:
                    b64_to_model(model, model_data["params"])
                    logger.info(f"   Model loaded ({len(model_data['params'])} parameter tensors)")

                # Train locally
                logger.info(f"🔄 Training locally for {args.epochs} epoch(s)...")
                start_time = time.time()
                train_loss, train_acc = train_local(model, train_loader, device, epochs=args.epochs)
                train_time = time.time() - start_time
                logger.info(f"   Training Loss: {train_loss:.4f}")
                logger.info(f"   Training Acc:  {train_acc:.2%}")
                logger.info(f"   Duration:      {train_time:.1f}s")

                # Evaluate
                logger.info("📊 Evaluating on test set...")
                eval_loss, eval_acc = evaluate(model, test_loader, device)
                logger.info(f"   Test Loss:     {eval_loss:.4f}")
                logger.info(f"   Test Accuracy: {eval_acc:.2%}")

                # Submit update
                logger.info("📤 Submitting trained weights to server...")
                submit_data = {
                    "client_id": client_id,
                    "params": model_to_b64(model),
                    "num_examples": len(train_loader.dataset),
                    "metrics": {
                        "accuracy": train_acc,
                        "loss": train_loss,
                        "eval_accuracy": eval_acc,
                        "eval_loss": eval_loss,
                        "train_time": train_time,
                        "device": str(device),
                        "ip": my_ip,
                    }
                }
                
                result = api_call("POST", f"{server}/api/v1/distributed/submit-update", 
                                  json=submit_data, timeout=180)
                
                if result.get("success"):
                    logger.info(f"✅ Server: {result.get('message', 'OK')}")
                else:
                    logger.warning(f"⚠️  Server rejected: {result.get('message', 'Unknown error')}")

                last_completed_round = current_round
                logger.info("")
            
            time.sleep(2)

        except KeyboardInterrupt:
            print()
            logger.info("👋 Client stopped by user. Goodbye!")
            break
        except requests.ConnectionError:
            logger.warning("Connection lost. Retrying in 10s...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
