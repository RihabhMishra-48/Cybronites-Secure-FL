import numpy as np
from typing import List, Tuple

def detect_anomaly(client_updates: List[List[np.ndarray]], threshold: float = 3.0) -> List[int]:
    """
    Detects anomalous client updates based on statistical distance 
    from the median of all updates (Z-score approach).
    
    Returns: List of indices of rejected clients.
    """
    if not client_updates:
        return []
        
    num_clients = len(client_updates)
    num_layers = len(client_updates[0])
    
    # Process layers individually and calculate their respective mean shifts
    # We'll use the mean of each layer's weights as the proxy for the update
    client_features = []
    for client_weights in client_updates:
        features = [float(np.mean(w)) for w in client_weights]
        client_features.append(features)
        
    client_features = np.array(client_features) # (num_clients, num_layers)
    
    # Calculate median and standard deviation across clients for each layer
    median_features = np.median(client_features, axis=0) # (num_layers,)
    std_features = np.std(client_features, axis=0) # (num_layers,)
    
    # Handle zero std to avoid division by zero
    std_features[std_features == 0] = 1e-6
    
    rejected_indices = []
    for i in range(num_clients):
        # Calculate Z-score for each layer of this client's update
        z_scores = np.abs((client_features[i] - median_features) / std_features)
        
        # If any layer's Z-score exceeds the threshold, mark the client as anomalous
        if np.any(z_scores > threshold):
            rejected_indices.append(i)
            
    return rejected_indices
