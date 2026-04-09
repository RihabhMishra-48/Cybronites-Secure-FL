"""
Pre-defined ML/DL Model Architectures for secure training.
Models adapt to dataset input shapes and number of classes dynamically.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleCNN(nn.Module):
    """
    Lightweight CNN for image classification.
    Suitable for MNIST, Fashion-MNIST, and small image datasets.
    """
    def __init__(self, input_channels: int = 1, num_classes: int = 10,
                 input_height: int = 28, input_width: int = 28):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.25)
        
        # Calculate flattened size after 3 pool layers
        h = input_height // 8  # 3 MaxPool2d(2,2)
        w = input_width // 8
        h = max(h, 1)
        w = max(w, 1)
        flat_size = 128 * h * w
        
        self.fc1 = nn.Linear(flat_size, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = x.flatten(1)
        x = self.dropout(F.relu(self.fc1(x)))
        return self.fc2(x)


class ResNet18(nn.Module):
    """
    Adapted ResNet-18 that works with varying input channel counts
    and spatial dimensions.
    """
    def __init__(self, input_channels: int = 1, num_classes: int = 10,
                 input_height: int = 28, input_width: int = 28):
        super().__init__()
        self.input_channels = input_channels
        
        # Initial convolution — adapted for small images
        self.conv1 = nn.Conv2d(input_channels, 64, 3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        
        # Residual blocks
        self.layer1 = self._make_layer(64, 64, 2)
        self.layer2 = self._make_layer(64, 128, 2, stride=2)
        self.layer3 = self._make_layer(128, 256, 2, stride=2)
        self.layer4 = self._make_layer(256, 512, 2, stride=2)
        
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def _make_layer(self, in_channels, out_channels, blocks, stride=1):
        layers = []
        layers.append(ResidualBlock(in_channels, out_channels, stride))
        for _ in range(1, blocks):
            layers.append(ResidualBlock(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = x.flatten(1)
        return self.fc(x)


class ResidualBlock(nn.Module):
    """Standard residual block with skip connection."""
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, 
                                stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3,
                                stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return F.relu(out)


class MLP(nn.Module):
    """
    Multi-Layer Perceptron — flattens input and runs through FC layers.
    Works with any input shape.
    """
    def __init__(self, input_channels: int = 1, num_classes: int = 10,
                 input_height: int = 28, input_width: int = 28):
        super().__init__()
        input_dim = input_channels * input_height * input_width
        
        self.network = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.network(x)


# ── Factory ─────────────────────────────────────────────────

MODEL_REGISTRY = {
    "SimpleCNN": SimpleCNN,
    "ResNet18": ResNet18,
    "MLP": MLP,
}


def create_model(model_type: str, input_channels: int = 1,
                 num_classes: int = 10, input_shape: list[int] = None) -> nn.Module:
    """
    Factory function to create a model by name.
    
    Args:
        model_type: One of 'SimpleCNN', 'ResNet18', 'MLP'
        input_channels: Number of input channels (1 for grayscale, 3 for RGB)
        num_classes: Number of output classes
        input_shape: [channels, height, width]
    """
    if model_type not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{model_type}'. Available: {list(MODEL_REGISTRY.keys())}"
        )
    
    if input_shape:
        input_channels = input_shape[0]
        h, w = input_shape[1], input_shape[2]
    else:
        h, w = 28, 28
    
    return MODEL_REGISTRY[model_type](
        input_channels=input_channels,
        num_classes=num_classes,
        input_height=h,
        input_width=w
    )
