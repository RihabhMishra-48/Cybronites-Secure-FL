"""
Secure Aggregation via Additive Secret Sharing (SMPC Simulation).

Implements a simplified Secure Multi-Party Computation protocol
where each client splits its model update into N additive shares.
The server receives and sums the shares — it can reconstruct the
*aggregate* but never sees any individual client's update.

    secret = share_1 + share_2 + ... + share_N

This provides:
    ✔ Input privacy: Server cannot read individual updates
    ✔ Correctness: Sum of shares equals original aggregate
    ✔ Lightweight: No heavy cryptographic operations (Paillier, etc.)
"""

import torch
from typing import Dict, List, Tuple


class SecretSharer:
    """
    Additive secret sharing for a single tensor.

    Given a secret tensor S, produce N shares such that:
        S = s_1 + s_2 + ... + s_N

    The first (N-1) shares are random; the last share is the
    residual S - sum(s_1 ... s_{N-1}).
    """

    @staticmethod
    def create_shares(
        secret: torch.Tensor,
        num_shares: int,
    ) -> List[torch.Tensor]:
        """
        Split a secret tensor into `num_shares` additive shares.

        Parameters
        ----------
        secret : torch.Tensor
            The value to be secret-shared.
        num_shares : int
            Number of shares to produce (>= 2).

        Returns
        -------
        shares : list of torch.Tensor
            Each share is the same shape as `secret`.
        """
        assert num_shares >= 2, "Need at least 2 shares."
        shares = []
        running_sum = torch.zeros_like(secret)
        for _ in range(num_shares - 1):
            share = torch.randn_like(secret)
            shares.append(share)
            running_sum += share
        # Last share ensures exact reconstruction
        shares.append(secret - running_sum)
        return shares

    @staticmethod
    def reconstruct(shares: List[torch.Tensor]) -> torch.Tensor:
        """Sum all shares to recover the original secret."""
        return sum(shares)


class SecureAggregator:
    """
    Orchestrates secure aggregation across multiple FL clients.

    Protocol:
        1. Each client locally creates N shares of its update.
        2. Each share_j is "sent to participant j" (simulated in-memory).
        3. The server collects the j-th share from every client and sums
           them → partial_sum_j.
        4. partial_sum_1 + ... + partial_sum_N = true aggregate.

    The server only ever sees partial sums — never any individual
    client's full update.
    """

    def __init__(self, num_clients: int):
        self.num_clients = num_clients

    def aggregate(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
    ) -> Dict[str, torch.Tensor]:
        """
        Securely aggregate a list of client updates.

        Parameters
        ----------
        client_updates : list of dict
            Each dict maps param_name → tensor update from one client.

        Returns
        -------
        aggregated : dict
            The average of all client updates (reconstructed from shares).
        """
        n = len(client_updates)
        if n == 0:
            return {}

        param_names = list(client_updates[0].keys())

        # --- Phase 1: Each client creates shares ---
        # all_shares[client_i][param_name] = list of N shares
        all_shares = []
        for update in client_updates:
            client_shares = {}
            for name in param_names:
                client_shares[name] = SecretSharer.create_shares(
                    update[name], num_shares=n
                )
            all_shares.append(client_shares)

        # --- Phase 2: Collect j-th share across all clients ---
        # partial_sums[param_name] = sum of all j-th shares (for each j)
        # Then sum across j → true aggregate
        aggregated = {}
        for name in param_names:
            total = torch.zeros_like(client_updates[0][name])
            for j in range(n):          # share index
                for i in range(n):      # client index
                    total += all_shares[i][name][j]
            # Average
            aggregated[name] = total / n

        return aggregated

    def verify_correctness(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
        secure_result: Dict[str, torch.Tensor],
        tolerance: float = 1e-5,
    ) -> bool:
        """
        Verify that secure aggregation produces the same result as
        plain averaging (for debugging / research validation).
        """
        param_names = list(client_updates[0].keys())
        for name in param_names:
            plain_avg = torch.mean(
                torch.stack([u[name] for u in client_updates]), dim=0
            )
            if not torch.allclose(plain_avg, secure_result[name],
                                  atol=tolerance):
                return False
        return True
