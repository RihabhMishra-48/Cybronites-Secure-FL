# API Reference

A detailed guide to the core classes and methods in the **Secure Federated Learning** framework.

## Federated Learning (`core/`)

### `GlobalServer`
The central model repository and management node.
*   `__init__(node_id, aggregator_type='median')`: Initialize the server with a robust aggregator.
*   `aggregate(updates_list)`: Aggregates weights from multiple clients.
*   `get_parameters()`: Returns current global model weights.
*   `set_parameters(new_params)`: Updates weights once consensus is reached.

### `LocalClient`
An individual participant in the distributed training.
*   `train(global_params, epochs=1)`: Update the model locally and applies DP (if configured).
*   `get_id()`: Return the client's unique identifier.

---

## Blockchain and Consensus (`blockchain/`)

### `Blockchain`
The ledger system maintaining the audit trail.
*   `add_transaction(tx)`: Queue a validation event to the pending pool.
*   `mine_pending_transactions()`: Create a new block using PoW difficulty.
*   `validate_chain()`: Verify the hash linkage and PoW across all blocks.
*   `print_chain()`: Human-readable dump of all transactions.

### `ValidationContract`
A set of security policies for update verification.
*   `validate_update(client_id, update, reference_median, ...)`: Check for hijacking (L2-norm) and poisoning (Cosine similarity).
*   `get_policy_details()`: Return current clipping and similarity thresholds.

### `ReputationManager`
Manages the scoring and blacklisting logic.
*   `record_valid_update(client_id)`: Reward participant for good behavior.
*   `record_malicious_update(client_id)`: Penalize for detected anomalies.
*   `is_blocked(client_id)`: Check if the client's score is below the threshold.

---

## Security Utilities (`security/`)

### `SecureAggregator`
Orchestrates SMPC-based aggregation (Additive Secret Sharing).
*   `aggregate(client_updates)`: Break updates into shares, sum them, and reconstruct the average.
*   `verify_correctness(client_updates, secure_result)`: compare SMPC output against plain averaging.

### `DPSpec`
Configuration for Differential Privacy.
*   `l2_norm_clip`: Maximum allowed magnitude for a gradient vector.
*   `noise_multiplier`: Standard deviation of the Gaussian noise relative to sensitivity.

---

## Data and Utils (`utils/`)

### `get_mnist_loaders(num_clients, batch_size=32)`
Downloads the MNIST dataset and splits it into $N$ non-overlapping, IID shards for the clinical simulation.
