# Security & Privacy Framework

This document details the security and privacy mechanisms implemented in the **Secure Federated Learning** system.

## Differential Privacy (DP)

We implement **Local Differential Privacy (LDP)** at the client level before any updates are sent to the server. This prevents the server or other participants from identifying specific training samples.

### Mechanism
*   **L2-Norm Clipping**: Every parameter update (gradient) is clipped if its norm exceeds a threshold $C$.
*   **Noise Injection**: Gaussian noise with zero mean and variance $(\sigma C)^2$ is added.
*   **DP Specification**: Managed through the `DPSpec` class in `security/privacy.py`.

```python
# Differential Privacy Implementation Strategy
clip_factor = min(1.0, dp_spec.l2_norm_clip / (total_norm + 1e-6))
noise_std = dp_spec.noise_multiplier * dp_spec.l2_norm_clip
noise = torch.randn_like(clipped_update) * noise_std
```

## Secure Multi-Party Computation (SMPC)

To ensure **Input Privacy** from the server itself, we use a simulation of Additive Secret Sharing (Secure Aggregation).

### Secure Aggregation Protocol
1.  **Secret Sharing**: Each client splits its trained global weights into $N$ shares ($N$ = number of participants).
2.  **Partial Sums**: The server receives one share from each client and sums them locally.
3.  **Reconstruction**: The sum of all partial sums across all clients reconstructs the *averaged global update*.
4.  **Privacy**: The server never sees an individual update, only the sum of shares.

## Defense Against Poisoning Attacks

We assume a hybrid threat model where a percentage of clients may be malicious (e.g., trying to poison the global model with bad weights).

### Multi-Layer Defense
1.  **Smart Contract Validation**:
    *   **L2-Norm Check**: Discards updates with abnormally large gradients.
    *   **Cosine Similarity**: Compares the client update with a coordinate-wise median (reference update). Updates that deviate too far are rejected.
2.  **Reputation System**:
    *   Maintains a persistent trust score for each node.
    *   Nodes that frequently submit rejected updates are penalized and eventually blacklisted.
3.  **Proof-of-Accuracy (PoA)**:
    *   Model updates are only applied if a set of "validator" nodes confirm that the new global model performs at least as well as the previous one (within a tolerance).

## Cryptographic Integrity (Blockchain)

The **Blockchain Ledger** provides a tamper-proof audit trail for every transaction.
*   **SHA-256 Hashing**: Ensures block integrity and linkage.
*   **Proof-of-Work (PoW)**: A simplified PoW (configurable difficulty) prevents easy history manipulation.
*   **Distributed Trust**: The ledger records "Who updated what, when, and with what reputation," making auditing straightforward for research purposes.
