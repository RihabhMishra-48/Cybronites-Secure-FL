"""
Blockchain Distributed Ledger for Federated Learning.

Implements an in-memory blockchain that records every model update
transaction. Uses SHA-256 hashing and a configurable difficulty
proof-of-work for block mining (kept low for simulation speed).

Stores per-transaction:
    client_id, model_hash, timestamp, validation_status, reputation_score
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Transaction:
    """A single ledger entry representing a client model-update event."""
    client_id: str
    model_hash: str
    timestamp: float
    validation_status: str          # "VALID" | "REJECTED"
    reputation_score: float
    round_number: int = 0
    dp_noise_applied: bool = False
    l2_norm: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Block:
    """A single block in the chain."""
    index: int
    timestamp: float
    transactions: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def compute_hash(self) -> str:
        """SHA-256 of the block contents (excluding the hash field itself)."""
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()


class Blockchain:
    """
    In-memory blockchain for Federated Learning audit trail.

    Parameters
    ----------
    difficulty : int
        Number of leading zeros required in block hash (PoW).
        Default 2 keeps mining fast for research simulations.
    """

    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self._create_genesis_block()

    # ------------------------------------------------------------------
    # Genesis
    # ------------------------------------------------------------------
    def _create_genesis_block(self):
        genesis = Block(
            index=0,
            timestamp=time.time(),
            transactions=[{"event": "GENESIS", "message": "Global Model Initialized"}],
            previous_hash="0" * 64,
        )
        genesis.hash = self._mine_block(genesis)
        self.chain.append(genesis)

    # ------------------------------------------------------------------
    # Mining (simplified PoW)
    # ------------------------------------------------------------------
    def _mine_block(self, block: Block) -> str:
        """Find a nonce such that hash starts with `difficulty` zeros."""
        target = "0" * self.difficulty
        while True:
            candidate = block.compute_hash()
            if candidate.startswith(target):
                return candidate
            block.nonce += 1

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------
    def add_transaction(self, tx: Transaction):
        """Queue a transaction into the pending pool."""
        self.pending_transactions.append(tx)

    def mine_pending_transactions(self) -> Block:
        """Create a new block from all pending transactions and mine it."""
        if not self.pending_transactions:
            return self.chain[-1]

        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=[tx.to_dict() for tx in self.pending_transactions],
            previous_hash=self.chain[-1].hash,
        )
        new_block.hash = self._mine_block(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_client_history(self, client_id: str) -> List[Dict]:
        """Return all transactions for a specific client across all blocks."""
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("client_id") == client_id:
                    history.append(tx)
        return history

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def get_chain_length(self) -> int:
        return len(self.chain)

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------
    def validate_chain(self) -> bool:
        """Walk the entire chain and verify hash linkage + PoW."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Re-compute hash
            if current.hash != current.compute_hash():
                return False
            # Verify linkage
            if current.previous_hash != previous.hash:
                return False
            # Verify PoW
            if not current.hash.startswith("0" * self.difficulty):
                return False
        return True

    # ------------------------------------------------------------------
    # Pretty print
    # ------------------------------------------------------------------
    def print_chain(self):
        """Human-readable chain dump for research logging."""
        print("\n" + "═" * 70)
        print("  BLOCKCHAIN LEDGER")
        print("═" * 70)
        for block in self.chain:
            print(f"\n  Block #{block.index}")
            print(f"  Hash:     {block.hash[:24]}...")
            print(f"  PrevHash: {block.previous_hash[:24]}...")
            print(f"  Nonce:    {block.nonce}")
            print(f"  Transactions ({len(block.transactions)}):")
            for tx in block.transactions:
                cid = tx.get("client_id", "SYSTEM")
                status = tx.get("validation_status", tx.get("event", "—"))
                rep = tx.get("reputation_score", "—")
                print(f"    ├─ {cid:<12} │ {status:<10} │ rep={rep}")
            print("  " + "─" * 50)
        print("═" * 70)
        print(f"  Chain length: {len(self.chain)} blocks  │  Valid: {self.validate_chain()}")
        print("═" * 70 + "\n")
