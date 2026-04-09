"""Blockchain-based Federated Learning infrastructure.

Provides an immutable distributed ledger, smart contract validation,
consensus mechanisms, and a reputation system for secure FL.
"""
from .ledger import Block, Blockchain
from .smart_contract import ValidationContract, AggregationContract, Transaction
from .consensus import ProofOfAccuracy
from .reputation import ReputationManager

__all__ = [
    'Block', 'Blockchain',
    'ValidationContract', 'AggregationContract', 'Transaction',
    'ProofOfAccuracy',
    'ReputationManager',
]
