import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset

def get_mnist(data_path="./data"):
    """
    Downloads and prepares the MNIST dataset.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    train_dataset = datasets.MNIST(data_path, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(data_path, train=False, download=True, transform=transform)
    
    return train_dataset, test_dataset

def partition_data(dataset, num_clients, client_id):
    """
    Partitions the dataset for a specific client (IID split).
    In a real scenario, this would be local data.
    """
    size = len(dataset) // num_clients
    indices = list(range(size * client_id, size * (client_id + 1)))
    return Subset(dataset, indices)

def load_data(client_id, num_clients=2, batch_size=32):
    """
    Loads partitioned MNIST training and test data for a given client.
    """
    train_dataset, test_dataset = get_mnist()
    
    # Simulating data partitioning across clients
    train_subset = partition_data(train_dataset, num_clients, client_id)
    
    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader
