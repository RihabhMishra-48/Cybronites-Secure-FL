import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import requests
import json
import time
import hashlib
import sys
import os

# To ensure we can import models from backend if needed, or just redefine small parts
# Here we redefine the model to keep the client script standalone
class MNISTModel(nn.Module):
    def __init__(self):
        super(MNISTModel, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = torch.relu(torch.max_pool2d(self.conv1(x), 2))
        x = torch.relu(torch.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = torch.relu(self.fc1(x))
        x = torch.dropout(x, training=self.training)
        x = self.fc2(x)
        return torch.log_softmax(x, dim=1)

API_URL = "http://127.0.0.1:8000"

def calculate_hash(weights_list):
    weights_json = json.dumps([w.tolist() for w in weights_list])
    return hashlib.sha256(weights_json.encode()).hexdigest()

def train_locally(model, epochs=1):
    model.train()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.5)
    
    # Generate synthetic local data (28x28 grayscale imgs)
    # In a real scenario, this would be a local dataset
    data = torch.randn(10, 1, 28, 28)
    target = torch.randint(0, 10, (10,))
    
    print(f"Training locally for {epochs} epochs...")
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(data)
        loss = torch.nn.functional.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch+1}: Loss = {loss.item():.4f}")
    
    return [param.data.cpu().numpy() for param in model.parameters()]

def run_client():
    print("AI GUARDIAN - REAL NODE STARTING...")
    name = input("Enter Node Name: ") or "Node_Alpha"
    
    # 1. Register
    try:
        resp = requests.post(f"{API_URL}/register", json={"name": name})
        node_id = resp.json()["node_id"]
        print(f"Registered successfully. ID: {node_id}")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return

    while True:
        # 2. Check Status
        try:
            status_resp = requests.get(f"{API_URL}/status").json()
            if status_resp["status"] == "WAITING":
                print(f"\n--- Round {status_resp['round']} In Progress ---")
                
                # 3. Download Global Model
                model_data = requests.get(f"{API_URL}/download-model").json()
                weights = [np.array(w) for w in json.loads(model_data["weights"])]
                
                model = MNISTModel()
                # Load weights
                params_dict = zip(model.state_dict().keys(), [torch.tensor(w) for w in weights])
                model.load_state_dict({k: v for k, v in params_dict})
                
                # 4. Train
                new_weights = train_locally(model)
                weight_hash = calculate_hash(new_weights)
                
                # 5. Submit
                print("Submitting updates to secure aggregator...")
                submit_resp = requests.post(f"{API_URL}/submit-update", json={
                    "node_id": node_id,
                    "weights": [w.tolist() for w in new_weights],
                    "hash": weight_hash
                })
                print(f"Server Response: {submit_resp.json()['status']}")
                
                # Wait for round to finish
                print("Waiting for next round...")
                while requests.get(f"{API_URL}/status").json()["status"] != "IDLE":
                    time.sleep(2)
            else:
                # Idle - wait
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(3)
        except Exception as e:
            print(f"\nConnection lost. Retrying... {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_client()
