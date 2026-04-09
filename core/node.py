import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleMLP(nn.Module):
    """A standard MLP for MNIST-like tasks."""
    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super(SimpleMLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = x.view(-1, 784)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class Node:
    """Base class for Federated Learning participants."""
    def __init__(self, node_id, model=None):
        self.node_id = node_id
        if model is None:
            self.model = SimpleMLP()
        else:
            self.model = model

    def get_parameters(self):
        return {name: param.data.clone() for name, param in self.model.named_parameters()}

    def set_parameters(self, parameters):
        for name, param in self.model.named_parameters():
            param.data = parameters[name].clone()
