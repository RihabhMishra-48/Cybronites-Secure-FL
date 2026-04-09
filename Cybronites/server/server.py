import flwr as fl
import sys
import os
import threading
import time
import logging

# Ensure project root is in path for blockchain and security imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from Cybronites.server.bridge import app, bridge, start_bridge
    from Cybronites.server.strategy import SecureFedAvg
    from blockchain.ledger import Blockchain
    from blockchain.reputation import ReputationManager
except ImportError:
    # Fallback for local execution within Cybronites/server
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from bridge import app, bridge, start_bridge
    from strategy import SecureFedAvg
    from blockchain.ledger import Blockchain
    from blockchain.reputation import ReputationManager

from Cybronites.utils.structured_logging import setup_structured_logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GuardianServer")
setup_structured_logging("GuardianServer")

import argparse

def main():
    """
    Main entry point for the Secure Federated Learning Backend.
    Starts the FastAPI Bridge and the Flower FL Server.
    """
    # 0. Parse Arguments
    parser = argparse.ArgumentParser(description="AI Guardian Server")
    parser.add_argument("--rounds", type=int, default=100, help="Number of FL rounds")
    parser.add_argument("--flower_port", type=int, default=8080, help="Flower gRPC port")
    args = parser.parse_args()

    # 1. Initialize Components
    logger.info(f"Initializing Orchestrator (Rounds: {args.rounds})...")
    ledger = Blockchain(difficulty=1)
    reputation = ReputationManager()

    # 2. Start Dashboard Bridge (FastAPI) in background
    bridge_port = int(os.environ.get("PORT", 7861))
    bridge_thread = threading.Thread(
        target=start_bridge, 
        args=(bridge_port,), 
        daemon=True
    )
    bridge_thread.start()
    
    time.sleep(2)
    bridge.broadcast_sync("LOG", "Backend components initialized. Waiting for secure nodes...")

    # 3. Configure Secure Strategy
    strategy = SecureFedAvg(
        blockchain=ledger,
        reputation=reputation,
        min_fit_clients=2,
        min_available_clients=2,
        aggregation_method="median"
    )

    # 4. Launch Flower gRPC Server
    flower_port = args.flower_port
    logger.info(f"Launching Flower Server on port {flower_port}...")
    
    server_config = fl.server.ServerConfig(num_rounds=args.rounds)
    
    try:
        # Increase gRPC max message size for "global use" (larger models/updates)
        fl.server.start_server(
            server_address=f"0.0.0.0:{flower_port}",
            config=server_config,
            strategy=strategy,
            grpc_max_message_length=512 * 1024 * 1024 # 512 MB
        )
    except Exception as e:
        logger.error(f"Flower Server crashed: {e}")
        bridge.broadcast_sync("LOG", f"CRITICAL: Flower Server Error: {e}")

    # 5. Keep bridge alive for results visualization
    logger.info("Training session complete. Maintaining dashboard bridge...")
    bridge.broadcast_sync("LOG", "SESSION_COMPLETE: All rounds finalized.")
    bridge.broadcast_sync("STAT_UPDATE", {"status": "FINISHED"})
    
    # Graceful shutdown handler
    def shutdown():
        logger.info("Shutting down Guardian Server...")
        sys.exit(0)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()
