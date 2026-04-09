import hashlib
import json
import time
from typing import List, Dict, Any

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions # Transactions will store model update info
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block, proof: str) -> bool:
        # Simple verification
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False
        # In a real blockchain, we'd check the POW/POS here
        self.chain.append(block)
        return True

    def add_new_transaction(self, transaction: Dict[str, Any]):
        self.unconfirmed_transactions.append(transaction)

    def mine(self) -> int:
        """
        In this simulation, 'mining' just creates a new block with unconfirmed transactions.
        """
        if not self.unconfirmed_transactions:
            return False
        
        last_block = self.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash
        )
        
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        return new_block.index

    def get_chain_dict(self):
        return [b.__dict__ for b in self.chain]
