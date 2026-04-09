"""
Blockchain-Based Secure Federated Learning — Full Simulation Demo.

This script demonstrates the complete research architecture:
    1. Global Model Initialization → Genesis Block
    2. Local Client Training with Differential Privacy
    3. Smart Contract Validation (L2 norm + cosine similarity)
    4. Blockchain Ledger Recording
    5. Reputation System (reward/penalty/blocking)
    6. Secure Aggregation (Additive Secret Sharing / SMPC)
    7. Proof-of-Accuracy Consensus
    8. Global Model Update + Broadcast

Run:
    python demo.py
"""

import sys
import os
import time

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np

from core.client import LocalClient
from core.server import GlobalServer
from core.node import SimpleMLP
from security.privacy import DPSpec
from security.defense import MaliciousClient
from security.secure_aggregation import SecureAggregator
from blockchain.ledger import Blockchain
from blockchain.smart_contract import ValidationContract, AggregationContract
from blockchain.reputation import ReputationManager
from blockchain.consensus import ProofOfAccuracy
from utils.data import get_mnist_loaders


# ======================================================================
#  Evaluation Helper
# ======================================================================

def evaluate(model, test_loader):
    """Compute accuracy of the model on the test set."""
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, target in test_loader:
            output = model(data)
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += len(data)
    return correct / total


# ======================================================================
#  Compute Reference Median Update (for smart-contract validation)
# ======================================================================

def compute_median_update(updates):
    """Coordinate-wise median across a list of parameter-update dicts."""
    if not updates:
        return None
    param_names = updates[0].keys()
    median = {}
    for name in param_names:
        stacked = torch.stack([u[name] for u in updates])
        median[name], _ = torch.median(stacked, dim=0)
    return median


# ======================================================================
#  Main Simulation
# ======================================================================

def run_simulation(
    num_clients: int = 5,
    num_rounds: int = 5,
    malicious_ratio: float = 0.2,
    use_privacy: bool = True,
    use_secure_agg: bool = True,
):
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║   BLOCKCHAIN-BASED SECURE FEDERATED LEARNING SIMULATION     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"   Clients: {num_clients} | Rounds: {num_rounds} "
          f"| Malicious: {malicious_ratio*100:.0f}% | DP: {use_privacy} "
          f"| SecureAgg: {use_secure_agg}\n")

    # ------------------------------------------------------------------
    # 1. Setup Infrastructure
    # ------------------------------------------------------------------
    client_loaders, test_loader = get_mnist_loaders(num_clients)
    server = GlobalServer(node_id="Server-0", aggregator_type='median')

    # Blockchain
    blockchain = Blockchain(difficulty=2)

    # Smart Contracts
    validation_contract = ValidationContract(
        norm_threshold=10.0,
        cosine_threshold=-0.3,
    )
    aggregation_contract = AggregationContract()

    # Reputation
    reputation = ReputationManager(
        initial_score=100.0, reward=10.0, penalty=25.0, threshold=30.0
    )

    # Privacy
    dp_spec = DPSpec(l2_norm_clip=1.0, noise_multiplier=0.1) if use_privacy else None

    # Secure Aggregation
    secure_agg = SecureAggregator(num_clients) if use_secure_agg else None

    # Consensus
    consensus = ProofOfAccuracy(tolerance=0.02, supermajority=2/3)

    # ------------------------------------------------------------------
    # 2. Initialize Clients
    # ------------------------------------------------------------------
    clients = []
    num_malicious = int(num_clients * malicious_ratio)
    for i in range(num_clients):
        is_malicious = i < num_malicious
        client = LocalClient(f"Client-{i}", client_loaders[i], dp_spec=dp_spec)
        reputation.register_client(f"Client-{i}")
        clients.append({'obj': client, 'malicious': is_malicious})

    # Accuracy tracking
    accuracy_history = []

    # ------------------------------------------------------------------
    # 3. Federated Training Rounds
    # ------------------------------------------------------------------
    for r in range(1, num_rounds + 1):
        print(f"\n{'─' * 60}")
        print(f"  🌀 ROUND {r}/{num_rounds}")
        print(f"{'─' * 60}")

        global_params = server.get_parameters()
        all_updates = []
        client_meta = []

        # --- Local Training ---
        for client_info in clients:
            client = client_info['obj']
            cid = client.node_id

            # Skip blocked clients
            if reputation.is_blocked(cid):
                print(f"  🔴 {cid} — BLOCKED (reputation too low)")
                continue

            update = client.train(global_params, epochs=1)

            if client_info['malicious']:
                update = MaliciousClient.poison_update(update, intensity=20.0)
                print(f"  ⚠️  {cid} — Injected POISONED update")
            else:
                print(f"  ✅ {cid} — Submitted secure update")

            all_updates.append(update)
            client_meta.append({'id': cid, 'malicious': client_info['malicious']})

        if not all_updates:
            print("  ❌ No updates received this round.")
            continue

        # --- Smart Contract Validation ---
        print(f"\n  📜 Smart Contract Validation:")
        reference_median = compute_median_update(all_updates)
        valid_updates = []
        for i, (update, meta) in enumerate(zip(all_updates, client_meta)):
            cid = meta['id']
            score = reputation.get_score(cid)

            is_valid, tx = validation_contract.validate_update(
                client_id=cid,
                update=update,
                reference_median=reference_median,
                current_reputation=score,
                round_number=r,
            )

            if is_valid:
                reputation.record_valid_update(cid)
                tx.reputation_score = reputation.get_score(cid)
                valid_updates.append(update)
                print(f"    ✅ {cid} — VALID  (L2={tx.l2_norm:.3f}, "
                      f"cos={tx.cosine_sim:.4f})")
            else:
                reputation.record_malicious_update(cid)
                tx.reputation_score = reputation.get_score(cid)
                print(f"    ❌ {cid} — REJECTED: {tx.rejection_reason}")

            # Record transaction on blockchain
            blockchain.add_transaction(tx)

        # --- Aggregation ---
        if valid_updates:
            if use_secure_agg and len(valid_updates) >= 2:
                print(f"\n  🔒 Secure Aggregation (SMPC) over "
                      f"{len(valid_updates)} valid updates...")
                aggregated = secure_agg.aggregate(valid_updates)
            else:
                print(f"\n  📊 Standard Aggregation over "
                      f"{len(valid_updates)} valid updates...")
                aggregated = aggregation_contract.execute_aggregation(
                    valid_updates
                )

            # Apply aggregated update to global model
            current_params = server.get_parameters()
            new_params = {
                name: current_params[name] + aggregated[name]
                for name in aggregated
            }

            # --- Consensus (Proof of Accuracy) ---
            old_model = SimpleMLP()
            old_model.load_state_dict(server.model.state_dict())

            new_model = SimpleMLP()
            new_state = {}
            for name, param in new_model.named_parameters():
                new_state[name] = new_params[name]
            for name, param in new_model.named_parameters():
                param.data = new_params[name].clone()

            # Use a subset of client loaders as validators
            val_loaders = client_loaders[:min(3, len(client_loaders))]
            accepted, votes = consensus.run_consensus(
                old_model, new_model, val_loaders
            )
            consensus.print_votes(votes, accepted)

            if accepted:
                server.set_parameters(new_params)
                print("  ✅ Global model updated (consensus passed)")
            else:
                print("  ❌ Update REJECTED by consensus — model unchanged")
        else:
            print("\n  ⚠️  No valid updates — model unchanged")

        # --- Mine Block ---
        block = blockchain.mine_pending_transactions()
        print(f"  ⛏️  Block #{block.index} mined "
              f"(hash: {block.hash[:16]}...)")

        # --- Evaluate ---
        acc = evaluate(server.model, test_loader)
        accuracy_history.append(acc)
        print(f"  📈 Test Accuracy: {acc*100:.2f}%")

    # ------------------------------------------------------------------
    # 4. Final Summary
    # ------------------------------------------------------------------
    print("\n\n")
    blockchain.print_chain()
    reputation.print_leaderboard()

    print("═" * 60)
    print("  ACCURACY OVER ROUNDS")
    print("═" * 60)
    for i, acc in enumerate(accuracy_history, 1):
        bar = "█" * int(acc * 40)
        print(f"  Round {i}: {bar} {acc*100:.2f}%")
    print("═" * 60)

    print(f"\n  ✅ Chain Valid: {blockchain.validate_chain()}")
    print(f"  📦 Total Blocks: {blockchain.get_chain_length()}")
    print("  🏁 Simulation Complete.\n")

    return accuracy_history, blockchain, reputation


if __name__ == "__main__":
    run_simulation(
        num_clients=5,
        num_rounds=3,
        malicious_ratio=0.2,
        use_privacy=True,
        use_secure_agg=True,
    )
