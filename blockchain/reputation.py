"""
Reputation System for Blockchain-based Federated Learning.

Each client starts with a base score. Valid contributions increase the
score; malicious or anomalous updates decrease it. Clients whose score
drops below a configurable threshold are blocked from further participation.

    score = score + reward       (valid update)
    score = score - penalty      (malicious / anomalous update)
    BLOCKED if score < threshold
"""

from typing import Dict, List, Tuple


class ReputationManager:
    """
    Manages trust scores for all participating FL clients.

    Parameters
    ----------
    initial_score : float
        Starting reputation for every new client (default 100.0).
    reward : float
        Points added per successful, validated update (default 10.0).
    penalty : float
        Points deducted per rejected / malicious update (default 25.0).
    threshold : float
        Minimum score to remain an active participant (default 30.0).
    """

    def __init__(
        self,
        initial_score: float = 100.0,
        reward: float = 10.0,
        penalty: float = 25.0,
        threshold: float = 30.0,
    ):
        self.initial_score = initial_score
        self.reward = reward
        self.penalty = penalty
        self.threshold = threshold
        self.scores: Dict[str, float] = {}
        self._history: Dict[str, List[Tuple[str, float]]] = {}  # event log

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_client(self, client_id: str):
        """Add a new client with the initial reputation score."""
        if client_id not in self.scores:
            self.scores[client_id] = self.initial_score
            self._history[client_id] = [("REGISTERED", self.initial_score)]

    # ------------------------------------------------------------------
    # Score mutations
    # ------------------------------------------------------------------
    def record_valid_update(self, client_id: str) -> float:
        """Reward a client for a valid, accepted model update."""
        self._ensure_registered(client_id)
        self.scores[client_id] += self.reward
        self._history[client_id].append(("VALID_UPDATE", self.scores[client_id]))
        return self.scores[client_id]

    def record_malicious_update(self, client_id: str) -> float:
        """Penalize a client for a rejected / anomalous update."""
        self._ensure_registered(client_id)
        self.scores[client_id] = max(0.0, self.scores[client_id] - self.penalty)
        self._history[client_id].append(("MALICIOUS_UPDATE", self.scores[client_id]))
        return self.scores[client_id]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def is_blocked(self, client_id: str) -> bool:
        """True if the client's reputation has fallen below the threshold."""
        self._ensure_registered(client_id)
        return self.scores[client_id] < self.threshold

    def get_score(self, client_id: str) -> float:
        self._ensure_registered(client_id)
        return self.scores[client_id]

    def get_leaderboard(self) -> List[Tuple[str, float, str]]:
        """Sorted list of (client_id, score, status) tuples."""
        board = []
        for cid, score in sorted(self.scores.items(), key=lambda x: -x[1]):
            status = "BLOCKED" if score < self.threshold else "ACTIVE"
            board.append((cid, score, status))
        return board

    def get_history(self, client_id: str) -> List[Tuple[str, float]]:
        """Return the full event log for a client."""
        return self._history.get(client_id, [])

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _ensure_registered(self, client_id: str):
        if client_id not in self.scores:
            self.register_client(client_id)

    # ------------------------------------------------------------------
    # Pretty print
    # ------------------------------------------------------------------
    def print_leaderboard(self):
        print("\n" + "═" * 50)
        print("  REPUTATION LEADERBOARD")
        print("═" * 50)
        for cid, score, status in self.get_leaderboard():
            icon = "🟢" if status == "ACTIVE" else "🔴"
            bar_len = int(score / self.initial_score * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"  {icon} {cid:<14} {bar} {score:6.1f}  [{status}]")
        print("═" * 50 + "\n")
