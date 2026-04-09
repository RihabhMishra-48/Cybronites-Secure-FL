import torch
from .node import Node

class GlobalServer(Node):
    """The central aggregator that maintains the global model state."""
    def __init__(self, node_id, aggregator_type='median'):
        super(GlobalServer, self).__init__(node_id)
        self.aggregator_type = aggregator_type

    def aggregate(self, updates_list):
        """
        Aggregates parameter updates from multiple clients.
        
        Supported Aggregators:
        1. 'average': Basic Federated Averaging (FedAvg). (Vulnerable to outliers)
        2. 'median': Coordinate-wise Median. (Robust to poisoned updates)
        3. 'trimmed_mean': Statistical Trimmed Mean. (Excludes outliers)
        """
        if not updates_list:
            return self.get_parameters()

        aggregated_updates = {}
        param_names = updates_list[0].keys()

        for name in param_names:
            # Stack updates for current parameter from all clients
            # shape: (num_clients, param_shape...)
            stacked_updates = torch.stack([updates[name] for updates in updates_list])
            
            if self.aggregator_type == 'average':
                 aggregated_updates[name] = torch.mean(stacked_updates, dim=0)
            elif self.aggregator_type == 'median':
                 aggregated_updates[name], _ = torch.median(stacked_updates, dim=0)
            elif self.aggregator_type == 'trimmed_mean':
                 # Compute trimmed mean (remove top/bottom 10% outliers)
                 # Note: Simple implementation for illustration
                 sorted_updates, _ = torch.sort(stacked_updates, dim=0)
                 trim_idx = int(0.1 * len(updates_list))
                 if trim_idx > 0:
                     trimmed = sorted_updates[trim_idx:-trim_idx]
                 else:
                     trimmed = sorted_updates
                 aggregated_updates[name] = torch.mean(trimmed, dim=0)
            else:
                 raise ValueError("Unsupported aggregator type.")

        # Update global model parameters
        current_params = self.get_parameters()
        new_params = {name: current_params[name] + aggregated_updates[name] for name in param_names}
        self.set_parameters(new_params)
        
        return new_params
