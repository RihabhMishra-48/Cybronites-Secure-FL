import torch
import numpy as np
import hashlib
import json
import logging
from typing import List, Dict, Any, Tuple
from .models import MNISTModel, get_model_parameters, set_model_parameters

logger = logging.getLogger(__name__)

class MLEngine:
    def __init__(self):
        self.global_model = MNISTModel()
        self.history = [] # To track training progress
        self.rejection_threshold = 20.0 # Adjusted for larger model weights

    def serialize_weights(self, weights: List[np.ndarray]) -> str:
        """Converts weights into a JSON string for hashing and storage."""
        # Convert each layer to list
        weights_list = [w.tolist() for w in weights]
        return json.dumps(weights_list)

    def calculate_hash(self, weight_str: str) -> str:
        """Calculates SHA-256 hash of the weight string."""
        return hashlib.sha256(weight_str.encode()).hexdigest()

    def detect_malicious(self, client_weights: List[np.ndarray]) -> bool:
        """
        Detects if a model update is malicious based on its distance 
        from the current global model.
        """
        global_params = get_model_parameters(self.global_model)
        
        distances = []
        for c_w, g_w in zip(client_weights, global_params):
            dist = np.linalg.norm(c_w - g_w)
            distances.append(dist)
        
        avg_dist = np.mean(distances)
        logger.info(f"Avg model distance: {avg_dist}")
        
        # In a real system, we'd use more complex poisoning detection 
        # like Krum, Trimmed Mean, or Median.
        # Here we use a simple Z-score threshold conceptually.
        return avg_dist > self.rejection_threshold

    def aggregate_updates(self, updates_list: List[List[np.ndarray]]) -> List[np.ndarray]:
        """
        Performs Federated Averaging (FedAvg).
        """
        if not updates_list:
            return []
            
        new_weights = []
        num_layers = len(updates_list[0])
        
        for layer_idx in range(num_layers):
            layer_updates = [update[layer_idx] for update in updates_list]
            avg_layer = np.mean(layer_updates, axis=0)
            new_weights.append(avg_layer)
            
        return new_weights

    def update_global_model(self, new_weights: List[np.ndarray]):
        """Uploads new weights to global model."""
        set_model_parameters(self.global_model, new_weights)

    def get_serialized_global_weights(self) -> str:
        """Returns the current global model weights as a serialized string."""
        weights = get_model_parameters(self.global_model)
        return self.serialize_weights(weights)
