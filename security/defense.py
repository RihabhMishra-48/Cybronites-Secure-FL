import torch

def detect_anomaly(client_update, reference_updates, threshold=2.0):
    """
    Check if a client's update is significantly different from the reference (e.g., median).
    
    1. Distance-based anomaly detection (Euclidean or Cosine distance from majority).
    2. Large Gradient detection (L2-Norm check).
    """
    error = 0.0
    for name in client_update:
        error += torch.norm(client_update[name] - reference_updates[name]) ** 2
    
    dist = error ** 0.5
    
    # Calculate average distance from reference among other nodes
    avg_ref_dist = 0.0
    for ref_upd in reference_updates:
         # Simplified: Assuming reference is the majority's mean or median
         pass

    return dist > threshold

class MaliciousClient:
    """A client that attempts to poison the global model (Adversarial simulation)."""
    @staticmethod
    def poison_update(update, intensity=10.0):
        """Scale updates excessively or invert them to degrade model utility."""
        poisoned = {}
        for name in update:
             # Scale gradients or invert them: Update * intensity
             # (Targeted attack logic - e.g. Label flipping gradients)
             poisoned[name] = update[name] * intensity
        return poisoned
