# 🛡️ Cybronites — Distributed Learning Client

Join a federated learning session from **any device, any network**.

## Quick Start

### 1. Install Python (3.9+)
Download from [python.org](https://www.python.org/downloads/)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Join a Training Session
```bash
python run_client.py \
  --server https://rishuuuuuu-cybronites-secure-fl.hf.space \
  --name "My-Device-Name"
```

That's it! The client will:
1. ✅ Register with the server
2. 📥 Download the global model
3. 🔄 Train locally on MNIST data
4. 📤 Upload trained weights
5. 🔁 Repeat for each round

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--server` | *(required)* | Server URL |
| `--name` | `Client-Node` | Display name for your device |
| `--epochs` | `1` | Local training epochs per round |
| `--batch-size` | `32` | Training batch size |

## Examples

```bash
# Basic usage
python run_client.py --server https://rishuuuuuu-cybronites-secure-fl.hf.space --name "Rishu-Laptop"

# More training per round
python run_client.py --server https://rishuuuuuu-cybronites-secure-fl.hf.space --name "Lab-PC" --epochs 3

# Local server (testing)
python run_client.py --server http://localhost:7860 --name "Test-Node"
```

## How It Works

```
┌─────────────────┐     HTTPS/REST      ┌──────────────────────┐
│   This Client   │ ◄─────────────────► │  HuggingFace Space   │
│   (Your Device) │                      │  (Central Server)    │
└─────────────────┘                      └──────────────────────┘
     │                                           │
     │ 1. Register                               │
     │ 2. Download model ◄───────────────────────│
     │ 3. Train locally                          │
     │ 4. Upload weights ───────────────────────►│
     │ 5. Wait for aggregation                   │
     │ 6. Repeat from step 2                     │
```

- **No special network setup** — works over standard HTTPS
- **No same-WiFi required** — any internet connection works
- **Data stays private** — only model weights are shared
- **Differential Privacy** — noise added to updates

## Requirements

- Python 3.9+
- ~200MB disk space (for PyTorch + MNIST data)
- Internet connection
