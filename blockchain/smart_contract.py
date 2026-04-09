"""
Smart Contracts for Blockchain-based Federated Learning.

ValidationContract
    Inspects each client's model update before it is accepted:
    1. L2-norm magnitude check (detects gradient scaling attacks)
    2. Cosine similarity check against the median update (detects inversion)
    If both pass → VALID. Otherwise → REJECTED.

AggregationContract
    Runs Federated Averaging (FedAvg) on the subset of validated updates.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import torch


# Re-export a lightweight Transaction for the smart-contract layer
@dataclass
class Transaction:
    """Immutable record of a model-update event."""
    client_id: str
    model_hash: str
    timestamp: float
    validation_status: str      # "VALID" | "REJECTED"
    reputation_score: float
    round_number: int = 0
    rejection_reason: str = ""
    l2_norm: float = 0.0
    cosine_sim: float = 0.0

    def to_dict(self):
        return asdict(self)


# ======================================================================
#  Helpers
# ======================================================================

def _compute_model_hash(update: Dict[str, torch.Tensor]) -> str:
    """SHA-256 fingerprint of a set of parameter tensors."""
    hasher = hashlib.sha256()
    for name in sorted(update.keys()):
        hasher.update(name.encode())
        hasher.update(update[name].cpu().numpy().tobytes())
    return hasher.hexdigest()


def _flatten(update: Dict[str, torch.Tensor]) -> torch.Tensor:
    """Flatten all parameter tensors into a single 1-D vector."""
    return torch.cat([v.flatten() for v in update.values()])


def _cosine_similarity(a: Dict[str, torch.Tensor],
                       b: Dict[str, torch.Tensor]) -> float:
    """Cosine similarity between two parameter update dicts."""
    va = _flatten(a)
    vb = _flatten(b)
    cos = torch.nn.functional.cosine_similarity(va.unsqueeze(0),
                                                 vb.unsqueeze(0))
    return cos.item()


def _l2_norm(update: Dict[str, torch.Tensor]) -> float:
    """Global L2 norm across all parameter tensors."""
    return torch.norm(_flatten(update)).item()


# ======================================================================
#  Validation Contract
# ======================================================================

class ValidationContract:
    """
    On-chain validation logic executed before an update is accepted.

    Parameters
    ----------
    norm_threshold : float
        Maximum allowed L2 norm for an update (default 10.0).
    cosine_threshold : float
        Minimum cosine similarity with median update (default -0.1).
        Negative value allows mild disagreement but catches inversions.
    """

    def __init__(self, norm_threshold: float = 10.0,
                 cosine_threshold: float = -0.1):
        self.norm_threshold = norm_threshold
        self.cosine_threshold = cosine_threshold

    def validate_update(
        self,
        client_id: str,
        update: Dict[str, torch.Tensor],
        reference_median: Optional[Dict[str, torch.Tensor]],
        current_reputation: float,
        round_number: int = 0,
    ) -> Tuple[bool, Transaction]:
        """
        Run validation checks and produce an immutable Transaction record.

        Returns
        -------
        (is_valid, transaction)
        """
        model_hash = _compute_model_hash(update)
        norm = _l2_norm(update)
        cos_sim = 0.0
        reason = ""

        # --- Check 1: L2 norm magnitude ---
        if norm > self.norm_threshold:
            reason = f"L2_NORM_EXCEEDED ({norm:.2f} > {self.norm_threshold})"
            tx = Transaction(
                client_id=client_id,
                model_hash=model_hash,
                timestamp=time.time(),
                validation_status="REJECTED",
                reputation_score=current_reputation,
                round_number=round_number,
                rejection_reason=reason,
                l2_norm=norm,
                cosine_sim=cos_sim,
            )
            return False, tx

        # --- Check 2: Cosine similarity with median ---
        if reference_median is not None:
            cos_sim = _cosine_similarity(update, reference_median)
            if cos_sim < self.cosine_threshold:
                reason = (f"COSINE_SIM_LOW ({cos_sim:.4f} "
                          f"< {self.cosine_threshold})")
                tx = Transaction(
                    client_id=client_id,
                    model_hash=model_hash,
                    timestamp=time.time(),
                    validation_status="REJECTED",
                    reputation_score=current_reputation,
                    round_number=round_number,
                    rejection_reason=reason,
                    l2_norm=norm,
                    cosine_sim=cos_sim,
                )
                return False, tx

        # --- Passed all checks ---
        tx = Transaction(
            client_id=client_id,
            model_hash=model_hash,
            timestamp=time.time(),
            validation_status="VALID",
            reputation_score=current_reputation,
            round_number=round_number,
            l2_norm=norm,
            cosine_sim=cos_sim,
        )
        return True, tx


# ======================================================================
#  Aggregation Contract
# ======================================================================

class AggregationContract:
    """
    On-chain aggregation logic.  Only processes updates that passed the
    ValidationContract.  Implements standard Federated Averaging.
    """

    @staticmethod
    def execute_aggregation(
        valid_updates: List[Dict[str, torch.Tensor]],
    ) -> Dict[str, torch.Tensor]:
        """
        FedAvg over accepted updates.

        Parameters
        ----------
        valid_updates : list of parameter-update dicts

        Returns
        -------
        aggregated : dict mapping param name → averaged tensor
        """
        if not valid_updates:
            return {}

        param_names = valid_updates[0].keys()
        aggregated = {}
        for name in param_names:
            stacked = torch.stack([u[name] for u in valid_updates])
            aggregated[name] = torch.mean(stacked, dim=0)
        return aggregated
