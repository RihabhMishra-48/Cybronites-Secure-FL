import torch

class DPSpec:
    """Differential Privacy Specification."""
    def __init__(self, l2_norm_clip=1.0, noise_multiplier=0.1):
        self.l2_norm_clip = l2_norm_clip
        self.noise_multiplier = noise_multiplier

def apply_dp_to_updates(updates, dp_spec):
    """
    Applies Differential Privacy to model updates (gradients or weight differences).
    
    1. L2-Norm Clipping: Ensures sensitivity of each client's update is bounded.
    2. Noise Injection: Adds Gaussian noise proportional to sensitivity.
    """
    total_norm = 0
    # Calculate global L2 norm of all parameter updates
    for param_name in updates:
        total_norm += torch.norm(updates[param_name]) ** 2
    total_norm = total_norm ** 0.5

    # Clipping factor
    clip_factor = min(1.0, dp_spec.l2_norm_clip / (total_norm + 1e-6))
    
    dp_updates = {}
    for param_name, param_update in updates.items():
        # Scale update if norm exceeds clip threshold
        clipped_update = param_update * clip_factor
        
        # Add Gaussian Noise: N(0, (sigma * C)^2)
        noise_std = dp_spec.noise_multiplier * dp_spec.l2_norm_clip
        noise = torch.randn_like(clipped_update) * noise_std
        
        dp_updates[param_name] = clipped_update + noise
        
    return dp_updates
