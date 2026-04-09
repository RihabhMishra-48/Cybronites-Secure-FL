"""
Proof-of-Accuracy Consensus Mechanism.

A novel consensus protocol for Federated Learning where validators
verify that a proposed model update improves (or at least does not
degrade) the model's accuracy on a held-out validation set.

Flow:
    1. Proposer submits a new aggregated model.
    2. N validators each evaluate old model vs new model on their
       local validation sets.
    3. Each validator votes ACCEPT if accuracy_new >= accuracy_old - tolerance.
    4. Block is accepted if a supermajority (>= 2/3) of validators approve.
"""

import torch
import torch.nn.functional as F
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Vote:
    """A single validator's decision."""
    validator_id: str
    accuracy_old: float
    accuracy_new: float
    decision: str               # "ACCEPT" | "REJECT"


class ProofOfAccuracy:
    """
    Consensus engine that validates model quality before committing
    a new block.

    Parameters
    ----------
    tolerance : float
        Maximum allowed accuracy drop (default 0.02 = 2%).
    supermajority : float
        Fraction of ACCEPT votes required (default 2/3).
    """

    def __init__(self, tolerance: float = 0.02, supermajority: float = 2/3):
        self.tolerance = tolerance
        self.supermajority = supermajority

    # ------------------------------------------------------------------
    # Evaluation helper
    # ------------------------------------------------------------------
    @staticmethod
    def _evaluate(model, data_loader) -> float:
        """Compute accuracy on a DataLoader."""
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for data, target in data_loader:
                output = model(data)
                pred = output.argmax(dim=1)
                correct += pred.eq(target).sum().item()
                total += len(data)
        return correct / total if total > 0 else 0.0

    # ------------------------------------------------------------------
    # Validator vote
    # ------------------------------------------------------------------
    def validator_vote(
        self,
        validator_id: str,
        old_model: torch.nn.Module,
        new_model: torch.nn.Module,
        val_loader,
    ) -> Vote:
        """
        A single validator evaluates old vs. new model and casts a vote.
        """
        acc_old = self._evaluate(old_model, val_loader)
        acc_new = self._evaluate(new_model, val_loader)

        decision = "ACCEPT" if acc_new >= acc_old - self.tolerance else "REJECT"
        return Vote(
            validator_id=validator_id,
            accuracy_old=acc_old,
            accuracy_new=acc_new,
            decision=decision,
        )

    # ------------------------------------------------------------------
    # Consensus round
    # ------------------------------------------------------------------
    def run_consensus(
        self,
        old_model: torch.nn.Module,
        new_model: torch.nn.Module,
        validator_loaders: List,
    ) -> Tuple[bool, List[Vote]]:
        """
        Execute a full consensus round across all validators.

        Parameters
        ----------
        old_model : current global model
        new_model : proposed updated global model
        validator_loaders : list of DataLoaders (one per validator)

        Returns
        -------
        (accepted, votes)
        """
        votes: List[Vote] = []
        for i, loader in enumerate(validator_loaders):
            v = self.validator_vote(f"Validator-{i}", old_model, new_model, loader)
            votes.append(v)

        accept_count = sum(1 for v in votes if v.decision == "ACCEPT")
        accepted = accept_count / len(votes) >= self.supermajority if votes else False

        return accepted, votes

    # ------------------------------------------------------------------
    # Pretty print
    # ------------------------------------------------------------------
    @staticmethod
    def print_votes(votes: List[Vote], accepted: bool):
        print("\n  ┌─────────────────────────────────────────────┐")
        print("  │         PROOF-OF-ACCURACY CONSENSUS         │")
        print("  ├─────────────────────────────────────────────┤")
        for v in votes:
            icon = "✅" if v.decision == "ACCEPT" else "❌"
            delta = v.accuracy_new - v.accuracy_old
            sign = "+" if delta >= 0 else ""
            print(f"  │ {icon} {v.validator_id:<14} "
                  f"old={v.accuracy_old:.3f}  new={v.accuracy_new:.3f}  "
                  f"Δ={sign}{delta:.3f} │")
        result = "✅ BLOCK ACCEPTED" if accepted else "❌ BLOCK REJECTED"
        print(f"  ├─────────────────────────────────────────────┤")
        print(f"  │ Result:  {result:<34} │")
        print(f"  └─────────────────────────────────────────────┘\n")
