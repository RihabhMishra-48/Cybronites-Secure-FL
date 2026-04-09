# AI Guardian: Secure Federated Learning Framework 🛡️

A real-world, decentralized Federated Learning (FL) system built with **Flower (flwr)** and **PyTorch**. 
This framework allows multiple clients to collaboratively train a global model on the **MNIST dataset** without sharing their raw data, while protecting the central server from malicious/poisoned updates.

---

## 🏗️ Architecture

- **Server**: Orchestrates rounds, aggregates model weights using **FedAvg**, and filters updates using **Security Strategies**.
- **Clients**: Train locally on dedicated data shards and submit model weight updates (not raw data).
- **Communication**: Distributed gRPC communication via the Flower framework.

---

## 🔐 Security Features

1. **Weight Hashing (SHA-256)**: Every model update is hashed before transmission. The server logs these hashes to ensure an immutable audit trail and verify client integrity.
2. **Anomaly Detection (Z-Score)**: The server calculates the statistical distribution of incoming updates. Any client whose weights deviate significantly (Z-score > threshold) is marked as potentially malicious and excluded from the aggregation.
3. **Privacy by Design**: Raw data never leaves the client's local environment.

---

## 🚀 Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python -m server.server
```

### 3. Run Clients (Open multiple terminals)
For 2 clients:
- **Terminal A**: `python -m client.client 0 2`
- **Terminal B**: `python -m client.client 1 2`

---

## 📊 Expected Output Logs

### Server Logs:
- `Round 1 | GLOBAL ACCURACY: 0.1534`
- `Round 2 | Client 0 | Weight Hash: a1b2c3d4...`
- `Round 3 | SECURITY ALERT: Rejected 1 malicious updates.`

### Client Logs:
- `AI GUARDIAN | STARTING CLIENT 0...`
- `Client 0 | Round starting training...`
- `Client 0 | Round evaluation -> Accuracy: 0.8521`

---

## 🛤️ Roadmap & Improvements
- [ ] **Opacus Integration**: Add Differential Privacy to prevent model inversion attacks.
- [ ] **Homomorphic Encryption**: Encrypt weight updates so the server can only see the aggregate.
- [ ] **Non-IID Support**: Advanced data partitioning to simulate real-world data skewness.
- [ ] **Persistence**: Save the global model as `.pth` after training rounds.
