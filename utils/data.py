import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset

def get_mnist_loaders(num_clients, batch_size=32):
    """Downloads MNIST and splits it into non-overlapping shards for clients."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    train_dataset = datasets.MNIST('../data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST('../data', train=False, transform=transform)
    
    # Simple IID split: each client gets (N / num_clients) samples
    indices = torch.randperm(len(train_dataset))
    shard_size = len(train_dataset) // num_clients
    
    client_loaders = []
    for i in range(num_clients):
        shard_indices = indices[i * shard_size : (i + 1) * shard_size]
        subset = Subset(train_dataset, shard_indices)
        client_loaders.append(DataLoader(subset, batch_size=batch_size, shuffle=True))
        
    test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)
    
    return client_loaders, test_loader
