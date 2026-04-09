# Secure AI Training Platform

A **privacy-first** ML/DL training platform where datasets remain encrypted at rest and are decrypted **only in RAM** during training. Users can train models without ever seeing or accessing raw data.

## Architecture

```
User → FastAPI API → Redis Queue → Training Worker → Encrypted Vault
                                        ↓
                                   Key Manager (decryption key)
                                        ↓
                                   RAM-only decrypt → Train → Save Model
                                        ↓
                                   Wipe Memory → Destroy Sandbox
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r secure_training_platform/requirements.txt
```

### 2. Provision encrypted datasets

```bash
python -m secure_training_platform.tools.provision_datasets
```

This downloads MNIST, Fashion-MNIST, and CIFAR-10, encrypts them with AES-256-GCM, and stores them in the vault.

### 3. Start the platform

```bash
python -m secure_training_platform.main
```

API will be available at `http://localhost:8100`  
Interactive docs at `http://localhost:8100/docs`

### 4. Submit a training job

```bash
curl -X POST http://localhost:8100/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "<DATASET_ID>",
    "model_type": "SimpleCNN",
    "epochs": 10,
    "batch_size": 32,
    "learning_rate": 0.001
  }'
```

### 5. Check training status

```bash
curl http://localhost:8100/api/v1/training_status/<JOB_ID>
```

## Docker Deployment

```bash
cd secure_training_platform/docker
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/datasets` | List available datasets |
| GET | `/api/v1/models` | List trained models |
| POST | `/api/v1/train` | Submit training job |
| GET | `/api/v1/training_status/{id}` | Job status + metrics |
| GET | `/api/v1/training_jobs` | List all jobs |
| GET | `/api/v1/models/{id}/download` | Download trained model |
| GET | `/health` | Health check |

## Security Features

- **AES-256-GCM** encryption for all datasets at rest
- **Double encryption** — dataset keys encrypted with master key
- **RAM-only decryption** — data never touches disk in plaintext
- **Secure memory wipe** — `ctypes.memset` zeroing after training
- **RBAC** — only training workers can access decryption keys
- **Full audit trail** — every key access and training job logged
- **Rate limiting** — 10 training jobs per minute per client
- **Docker isolation** — containers destroyed after training

## Supported Models

- **SimpleCNN** — Lightweight 3-layer CNN
- **ResNet18** — Adapted ResNet with skip connections
- **MLP** — Multi-layer perceptron
