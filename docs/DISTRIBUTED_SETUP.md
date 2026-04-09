# 🌐 Distributed Deployment Guide

This guide explains how to transition from a local simulation to a truly distributed Federated Learning environment using multiple machines.

---

## 🏗️ 1. Server Setup (Machine A)

The server machine hosts the **Flower FL Server** and the **FastAPI Bridge**.

### Prerequisites
- Python 3.9+ installed and dependencies from `requirements.txt`.
- Open ports **7880** (Bridge) and **8095** (FL Server) in your Firewall.

### Execution
Run the orchestrator on the server machine:
```bash
# Set PORT and start the backend
# Use 0.0.0.0 to listen on all network interfaces
python run_local.py
```

> [!TIP]
> Note down the **Local Network IP** of this machine (e.g., `192.168.1.15`). You can find it using `ipconfig` on Windows or `ifconfig` on Linux.

---

## 💻 2. Client Setup (Machine B, C, ...)

Clients can run on any machine that can "ping" the server's IP.

### Execution
Run the client script and point it to the Server's IP:
```bash
# Syntax: python -m Cybronites.client.client <client_id> <total_clients> <server_ip>
python -m Cybronites.client.client 0 2 192.168.1.15
```

Alternatively, use environment variables:
```bash
# Windows (PowerShell)
$env:FL_SERVER_IP="192.168.1.15"; python -m Cybronites.client.client 0 2

# Linux/Mac
export FL_SERVER_IP=192.168.1.15
python -m Cybronites.client.client 0 2
```

---

## 📊 3. Dashboard Setup (Remote Access)

To view the dashboard from a different machine or point it to a remote backend:

### Development Mode
If you are running the dashboard via `npm run dev`:
1. Create a `.env.local` file in the `dashboard/` directory.
2. Add the following:
   ```env
   VITE_BACKEND_IP=192.168.1.15
   VITE_BACKEND_PORT=7880
   ```
3. Restart the dashboard: `npm run dev`.

---

## 🛡️ Firewall & Network Troubleshooting

If clients cannot connect:
1. **Ping Test**: Ensure Machine B can ping Machine A (`ping 192.168.1.15`).
2. **Port Check**: Ensure port **8095** is not blocked by Windows Defender or any other firewall.
3. **Subnet**: Ensure both machines are on the same subnet (e.g., connected to the same Wi-Fi router).

---
