#!/usr/bin/env python3
"""
Cybronites Multi-Client Runner
Runs 2-5 clients SIMULTANEOUSLY from one machine to simulate
multi-device distributed federated learning.

Usage:
    python run_multi_client.py --server https://rishuuuuuu-cybronites-secure-fl.hf.space --clients 3
    python run_multi_client.py --server http://localhost:7860 --clients 5 --epochs 2
"""

import argparse
import threading
import time
import sys
import os
import io
import base64
import logging
import urllib.request
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import requests
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset

# ── Logging setup: each client gets a colored prefix ──
LOG_COLORS = [
    "\033[94m",  # Blue
    "\033[92m",  # Green
    "\033[93m",  # Yellow
    "\033[95m",  # Magenta
    "\033[96m",  # Cyan
]
RESET = "\033[0m"

def make_logger(name, color):
    fmt = f"{color}[{name}]{RESET} %(asctime)s | %(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
        logger.addHandler(h)
    return logger


# ── Model (must match server) ──
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


# ── Data: partition MNIST among N clients ──
def load_partition(client_idx, num_clients, batch_size=32):
    """Each client gets a non-overlapping slice of MNIST training data."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    full_train = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_set   = datasets.MNIST(data_dir, train=False, download=True, transform=transform)

    # Partition: client i gets indices [i, i+num_clients, i+2*num_clients, ...]
    indices = list(range(client_idx, len(full_train), num_clients))
    subset  = Subset(full_train, indices)

    train_loader = DataLoader(subset, batch_size=batch_size, shuffle=True)
    test_loader  = DataLoader(test_set, batch_size=1000, shuffle=False)
    return train_loader, test_loader, len(indices)


# ── Serialization ──
def model_to_b64(model):
    result = []
    for val in model.state_dict().values():
        arr = val.cpu().detach().numpy()
        buf = io.BytesIO()
        np.save(buf, arr)
        result.append({"data": base64.b64encode(buf.getvalue()).decode()})
    return result

def b64_to_model(model, b64_list):
    state_dict = model.state_dict()
    for (key, _), item in zip(state_dict.items(), b64_list):
        buf = io.BytesIO(base64.b64decode(item["data"]))
        state_dict[key] = torch.from_numpy(np.load(buf))
    model.load_state_dict(state_dict)


# ── Network ──
def api(method, url, json=None, retries=5, timeout=120):
    for attempt in range(retries):
        try:
            resp = (requests.get(url, timeout=timeout) if method == "GET"
                    else requests.post(url, json=json, timeout=timeout))
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
            else:
                raise


# ── Single Client Thread ──
def run_client(client_idx, num_clients, server, name, epochs, device, results):
    color  = LOG_COLORS[client_idx % len(LOG_COLORS)]
    logger = make_logger(name, color)

    try:
        # Register
        reg = api("POST", f"{server}/api/v1/distributed/register",
                  json={"name": name, "ip": f"local-{client_idx}"})
        if not reg.get("success"):
            logger.error(f"Registration failed: {reg}")
            return

        client_id = reg["client_id"]
        logger.info(f"Registered | ID: {client_id} | Status: {reg.get('session_status')}")

        # Load partitioned data
        train_loader, test_loader, n_samples = load_partition(client_idx, num_clients)
        logger.info(f"Data partition: {n_samples} samples")

        model = MNISTNet().to(device)
        last_round = 0

        while True:
            try:
                status = api("GET", f"{server}/api/v1/distributed/status")
                cur_status = status.get("status", "IDLE")
                cur_round  = status.get("round", 0)
                total      = status.get("total_rounds", 0)

                if cur_status == "IDLE":
                    sys.stdout.write(f"\r{color}[{name}]{RESET} Waiting for session...")
                    sys.stdout.flush()
                    time.sleep(3)
                    continue

                if cur_status == "COMPLETE":
                    acc_hist = status.get("accuracy_history", [])
                    logger.info(f"Session COMPLETE | Final Acc: {acc_hist[-1]:.2%}" if acc_hist else "Session COMPLETE")
                    results[name] = {"status": "COMPLETE", "accuracy": acc_hist[-1] if acc_hist else 0}
                    time.sleep(5)
                    continue

                if cur_status in ("AGGREGATING",):
                    time.sleep(2)
                    continue

                if cur_status == "WAITING" and cur_round > last_round:
                    print()
                    logger.info(f"Round {cur_round}/{total} | Downloading model...")

                    model_data = api("GET", f"{server}/api/v1/distributed/get-model")
                    if "params" in model_data:
                        b64_to_model(model, model_data["params"])

                    # Train
                    logger.info(f"Training {epochs} epoch(s) on {n_samples} samples...")
                    model.train()
                    opt = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
                    correct = total_n = 0
                    last_loss = 0.0
                    t0 = time.time()

                    for _ in range(epochs):
                        for data, target in train_loader:
                            data, target = data.to(device), target.to(device)
                            opt.zero_grad()
                            out = model(data)
                            loss = F.nll_loss(out, target)
                            loss.backward()
                            opt.step()
                            last_loss = loss.item()
                            correct += out.argmax(1).eq(target).sum().item()
                            total_n += len(target)

                    train_acc = correct / total_n if total_n else 0
                    train_time = time.time() - t0
                    logger.info(f"Train done | Loss: {last_loss:.4f} | Acc: {train_acc:.2%} | {train_time:.1f}s")

                    # Eval
                    model.eval()
                    eval_correct = eval_total = eval_loss = 0
                    with torch.no_grad():
                        for data, target in test_loader:
                            data, target = data.to(device), target.to(device)
                            out = model(data)
                            eval_loss   += F.nll_loss(out, target, reduction='sum').item()
                            eval_correct += out.argmax(1).eq(target).sum().item()
                            eval_total   += len(target)
                    eval_acc = eval_correct / eval_total if eval_total else 0
                    logger.info(f"Test Acc: {eval_acc:.2%}")

                    # Submit
                    logger.info("Uploading weights...")
                    result = api("POST", f"{server}/api/v1/distributed/submit-update", json={
                        "client_id": client_id,
                        "params": model_to_b64(model),
                        "num_examples": n_samples,
                        "metrics": {
                            "accuracy": train_acc,
                            "loss": last_loss,
                            "eval_accuracy": eval_acc,
                            "device": str(device),
                            "ip": f"local-thread-{client_idx}",
                        }
                    }, timeout=180)

                    if result.get("success"):
                        logger.info(f"Server: {result.get('message')}")
                    else:
                        logger.warning(f"Rejected: {result.get('message')}")

                    last_round = cur_round

                time.sleep(2)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.warning(f"Error: {e} — retrying in 5s")
                time.sleep(5)

    except Exception as e:
        logger.error(f"Fatal: {e}")


# ── Main ──
def main():
    parser = argparse.ArgumentParser(description="Cybronites Multi-Client Simulator")
    parser.add_argument("--server",  required=True,          help="Server URL")
    parser.add_argument("--clients", type=int, default=2,    help="Number of parallel clients (2-5)")
    parser.add_argument("--epochs",  type=int, default=1,    help="Local epochs per round")
    parser.add_argument("--names",   nargs="*",              help="Custom names (optional)")
    args = parser.parse_args()

    n       = max(1, min(5, args.clients))
    server  = args.server.rstrip("/")
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Default names if not provided
    default_names = ["Alpha-Node", "Beta-Node", "Gamma-Node", "Delta-Node", "Epsilon-Node"]
    names = args.names if args.names else default_names[:n]
    names = (names + default_names)[:n]  # pad if fewer names given

    print("=" * 60)
    print(f"  CYBRONITES MULTI-CLIENT SIMULATOR")
    print(f"  Server  : {server}")
    print(f"  Clients : {n}  ({', '.join(names)})")
    print(f"  Device  : {device}")
    print(f"  Epochs  : {args.epochs}")
    print("=" * 60)
    print()

    # Health check
    try:
        h = api("GET", f"{server}/api/health")
        print(f"  Server ONLINE | {h}")
    except Exception as e:
        print(f"  ERROR: Cannot reach server — {e}")
        sys.exit(1)

    # Pre-download MNIST once (before threads start)
    print("  Pre-downloading MNIST dataset...")
    transform = transforms.Compose([transforms.ToTensor()])
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    datasets.MNIST(data_dir, train=False, download=True, transform=transform)
    print("  Dataset ready!\n")

    results = {}
    threads = []

    for i in range(n):
        t = threading.Thread(
            target=run_client,
            args=(i, n, server, names[i], args.epochs, device, results),
            daemon=True,
            name=names[i]
        )
        threads.append(t)
        t.start()
        time.sleep(1)  # stagger start slightly so logs don't collide

    print(f"  {n} client threads running! Press Ctrl+C to stop.\n")

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n  Stopping all clients...")

    print("\n  Results:")
    for name, r in results.items():
        print(f"    {name}: {r}")


if __name__ == "__main__":
    main()
