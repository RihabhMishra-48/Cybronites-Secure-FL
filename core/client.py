import torch
import torch.optim as optim
from .node import Node
from security.privacy import apply_dp_to_updates

class LocalClient(Node):
    """A Federated Learning client that performs training locally."""
    def __init__(self, node_id, data_loader, model=None, dp_spec=None):
        super(LocalClient, self).__init__(node_id, model)
        self.data_loader = data_loader
        self.dp_spec = dp_spec
        self.optimizer = optim.SGD(self.model.parameters(), lr=0.01)

    def train(self, global_parameters, epochs=1):
        """Perform training on local shard using global model weights."""
        # 1. Sync local model with global parameters
        self.set_parameters(global_parameters)
        
        # 2. Local Training Loop
        self.model.train()
        for epoch in range(epochs):
            for data, target in self.data_loader:
                self.optimizer.zero_grad()
                output = self.model(data)
                loss = torch.nn.functional.cross_entropy(output, target)
                loss.backward()
                self.optimizer.step()
        
        # 3. Compute parameter updates (New Weights - Old Weights)
        # Note: We share parameter updates, not the raw parameters.
        updates = {}
        for name, param in self.model.named_parameters():
             updates[name] = param.data.clone() - global_parameters[name].clone()
        
        # 4. Apply Privacy Mechanisms (Differential Privacy) if specified
        if self.dp_spec is not None:
             updates = apply_dp_to_updates(updates, self.dp_spec)
        
        return updates
