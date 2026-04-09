import hashlib
import numpy as np
import json
from typing import List

def hash_model_weights(weights: List[np.ndarray]) -> str:
    """
    Calculates the SHA-256 hash of the model weights.
    Used for verifying identity and integrity of client updates.
    """
    # Convert weights to list and then to JSON string for consistent hashing
    weights_list = [w.tolist() for w in weights]
    weights_json = json.dumps(weights_list, sort_keys=True)
    
    return hashlib.sha256(weights_json.encode()).hexdigest()

def verify_hash(weights: List[np.ndarray], expected_hash: str) -> bool:
    """
    Verifies the integrity of received weights against an expected hash.
    """
    current_hash = hash_model_weights(weights)
    return current_hash == expected_hash

def get_weight_summaries(weights: List[np.ndarray]) -> List[float]:
    """
    Extracts high-level statistical summaries for each layer of weights.
    Helps in detecting anomalies without examining every single parameter.
    """
    return [float(np.mean(w)) for w in weights]
