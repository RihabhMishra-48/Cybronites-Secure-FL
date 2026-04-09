"""
Dataset Provisioning Tool — Encrypts and registers real datasets into the vault.

Downloads popular datasets from torchvision, encrypts them with AES-256-GCM,
and registers them in the platform. Deletes raw data after encryption.

Usage:
    python -m secure_training_platform.tools.provision_datasets
"""

import io
import sys
import pickle
import logging
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))

from secure_training_platform.database.db import init_db
from secure_training_platform.key_manager.manager import KeyManager
from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.config import SUPPORTED_MODELS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


DATASETS_TO_PROVISION = [
    {
        "name": "MNIST",
        "description": "Handwritten digit recognition (0-9). 60,000 training images, 28x28 grayscale.",
        "torchvision_class": "MNIST",
        "num_classes": 10,
        "input_shape": [1, 28, 28],
        "allowed_models": SUPPORTED_MODELS
    },
    {
        "name": "Fashion-MNIST",
        "description": "Fashion product classification. 60,000 training images, 28x28 grayscale. 10 categories.",
        "torchvision_class": "FashionMNIST",
        "num_classes": 10,
        "input_shape": [1, 28, 28],
        "allowed_models": SUPPORTED_MODELS
    },
    {
        "name": "CIFAR-10",
        "description": "Object recognition across 10 classes. 50,000 training images, 32x32 RGB.",
        "torchvision_class": "CIFAR10",
        "num_classes": 10,
        "input_shape": [3, 32, 32],
        "allowed_models": SUPPORTED_MODELS
    },
]


def download_and_serialize(ds_config: dict) -> tuple[bytes, int]:
    """
    Download dataset from torchvision and serialize to bytes.
    Returns (serialized_bytes, num_samples).
    """
    import torchvision
    import torchvision.transforms as T
    import tempfile
    import shutil
    
    tmp_dir = tempfile.mkdtemp()
    
    try:
        logger.info(f"Downloading {ds_config['name']}...")
        
        dataset_class = getattr(torchvision.datasets, ds_config["torchvision_class"])
        dataset = dataset_class(root=tmp_dir, train=True, download=True)
        
        # Extract data and labels as numpy arrays
        if hasattr(dataset, 'data'):
            data = np.array(dataset.data)
        else:
            # Fallback for datasets without .data attribute
            data = np.array([np.array(img) for img, _ in dataset])
        
        if hasattr(dataset, 'targets'):
            labels = np.array(dataset.targets)
        else:
            labels = np.array([label for _, label in dataset])
        
        num_samples = len(data)
        
        # Serialize using pickle
        payload = {"data": data, "labels": labels}
        serialized = pickle.dumps(payload)
        
        logger.info(
            f"  {ds_config['name']}: {num_samples} samples, "
            f"{len(serialized)} bytes serialized"
        )
        
        return serialized, num_samples
        
    finally:
        # Delete raw downloaded data
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logger.info(f"  Cleaned raw download for {ds_config['name']}")


def provision_all():
    """Provision all datasets into the encrypted vault."""
    logger.info("=" * 60)
    logger.info("  Dataset Provisioning Tool")
    logger.info("=" * 60)
    
    # Initialize database
    init_db()
    
    # Initialize services
    key_manager = KeyManager()
    vault = DatasetVault(key_manager)
    
    # Check existing datasets
    existing = {d["name"] for d in vault.list_datasets()}
    
    for ds_config in DATASETS_TO_PROVISION:
        name = ds_config["name"]
        
        if name in existing:
            logger.info(f"⏭  {name} already registered, skipping")
            continue
        
        try:
            # Download and serialize
            raw_bytes, num_samples = download_and_serialize(ds_config)
            
            # Register in vault (encrypts and stores)
            dataset_id = vault.register_dataset(
                name=name,
                description=ds_config["description"],
                raw_data=raw_bytes,
                allowed_models=ds_config["allowed_models"],
                num_classes=ds_config["num_classes"],
                input_shape=ds_config["input_shape"],
                num_samples=num_samples
            )
            
            # Wipe raw bytes
            raw_bytes = b'\x00' * len(raw_bytes)
            del raw_bytes
            
            logger.info(f"✅ {name} encrypted and registered (ID: {dataset_id})")
            
        except Exception as e:
            logger.error(f"❌ Failed to provision {name}: {e}", exc_info=True)
    
    # Summary
    datasets = vault.list_datasets()
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"  Vault contains {len(datasets)} datasets:")
    for ds in datasets:
        logger.info(f"    • {ds['name']} — {ds['num_samples']} samples, {ds['dataset_size']} bytes encrypted")
    logger.info("=" * 60)


if __name__ == "__main__":
    provision_all()
