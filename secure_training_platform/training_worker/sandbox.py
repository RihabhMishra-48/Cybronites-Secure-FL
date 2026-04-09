"""
Training Sandbox — Secure in-memory training pipeline.

The entire dataset lifecycle happens in RAM:
1. Load encrypted bytes from vault
2. Decrypt in memory
3. Parse into tensors
4. Train model
5. Securely wipe all decrypted data
"""

import io
import json
import pickle
import logging
import time
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.training_worker.models import create_model
from secure_training_platform.training_worker.secure_memory import (
    secure_wipe_buffer, secure_wipe_tensor, SecureDataScope
)
from secure_training_platform.model_registry.registry import ModelRegistry
from secure_training_platform.database.db import execute_insert

logger = logging.getLogger(__name__)


class TrainingSandbox:
    """
    Isolated training environment that guarantees:
    - Decrypted data exists ONLY in RAM
    - All sensitive data is wiped after training
    - Training metrics are captured and saved
    """

    def __init__(self, vault: DatasetVault, registry: ModelRegistry):
        self.vault = vault
        self.registry = registry
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def run_training(self, job_id: str, dataset_id: str, model_type: str,
                     hyperparams: dict, progress_callback=None) -> dict:
        """
        Execute a complete training job inside a secure sandbox.
        
        Args:
            job_id: Unique job identifier
            dataset_id: Dataset to train on
            model_type: Model architecture name
            hyperparams: {epochs, batch_size, learning_rate}
            progress_callback: Optional fn(progress: float, metrics: dict)
        
        Returns:
            dict with {accuracy, loss, model_id, duration}
        """
        epochs = hyperparams.get("epochs", 10)
        batch_size = hyperparams.get("batch_size", 32)
        learning_rate = hyperparams.get("learning_rate", 0.001)
        
        start_time = time.time()
        decrypted_buffer = None
        train_data = None
        train_labels = None
        
        try:
            # ── Step 1: Decrypt dataset in memory ──────────────
            logger.info(f"[Job {job_id}] Decrypting dataset {dataset_id} to RAM...")
            decrypted_buffer = self.vault.decrypt_dataset_to_memory(
                dataset_id, requester="training_worker"
            )

            # Audit log for decryption event
            execute_insert(
                """INSERT INTO audit_log (event_type, actor, details)
                   VALUES (?, ?, ?)""",
                ("DATA_DECRYPTION", "sandbox", json.dumps({
                    "job_id": job_id,
                    "dataset_id": dataset_id,
                    "timestamp": datetime.utcnow().isoformat()
                }))
            )
            
            # ── Step 2: Parse bytes into tensors ───────────────
            logger.info(f"[Job {job_id}] Parsing decrypted data into tensors...")
            dataset_info = self.vault.get_dataset_info(dataset_id)
            raw_data = pickle.loads(decrypted_buffer.read())
            
            # Immediately wipe the decrypted buffer
            secure_wipe_buffer(decrypted_buffer)
            decrypted_buffer = None
            
            # Extract tensors from the parsed data
            if isinstance(raw_data, dict):
                train_data = torch.tensor(raw_data["data"], dtype=torch.float32)
                train_labels = torch.tensor(raw_data["labels"], dtype=torch.long)
            elif isinstance(raw_data, tuple) and len(raw_data) == 2:
                train_data = torch.tensor(raw_data[0], dtype=torch.float32)
                train_labels = torch.tensor(raw_data[1], dtype=torch.long)
            else:
                raise ValueError("Unsupported dataset format")
            
            # Clear the raw parsed data
            del raw_data
            
            # Normalize data to [0, 1]
            if train_data.max() > 1.0:
                train_data = train_data / 255.0
            
            # Reshape if needed: ensure [N, C, H, W]
            input_shape = dataset_info.get("input_shape", [1, 28, 28])
            if len(train_data.shape) == 3:
                train_data = train_data.unsqueeze(1)  # Add channel dim
            
            num_classes = dataset_info.get("num_classes", 10)
            
            logger.info(
                f"[Job {job_id}] Data shape: {train_data.shape}, "
                f"Labels: {train_labels.shape}, Classes: {num_classes}"
            )
            
            # ── Step 3: Create data loader ─────────────────────
            dataset = TensorDataset(train_data, train_labels)
            
            # Split 80/20 for train/val
            train_size = int(0.8 * len(dataset))
            val_size = len(dataset) - train_size
            train_set, val_set = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )
            
            train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
            
            # ── Step 4: Create model ───────────────────────────
            model = create_model(
                model_type, num_classes=num_classes, input_shape=input_shape
            )
            model = model.to(self.device)
            
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
            
            # ── Step 5: Training loop ──────────────────────────
            logger.info(f"[Job {job_id}] Training {model_type} for {epochs} epochs...")
            best_accuracy = 0.0
            best_loss = float('inf')
            
            for epoch in range(epochs):
                model.train()
                running_loss = 0.0
                correct = 0
                total = 0
                
                for batch_x, batch_y in train_loader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    
                    running_loss += loss.item()
                    _, predicted = outputs.max(1)
                    total += batch_y.size(0)
                    correct += predicted.eq(batch_y).sum().item()
                
                scheduler.step()
                
                train_loss = running_loss / len(train_loader)
                train_acc = 100.0 * correct / total
                
                # Validation
                val_acc, val_loss = self._evaluate(model, val_loader, criterion)
                
                if val_acc > best_accuracy:
                    best_accuracy = val_acc
                    best_loss = val_loss
                
                # Report progress
                progress = (epoch + 1) / epochs
                metrics = {
                    "epoch": epoch + 1,
                    "train_loss": round(train_loss, 4),
                    "train_acc": round(train_acc, 2),
                    "val_loss": round(val_loss, 4),
                    "val_acc": round(val_acc, 2)
                }
                
                if progress_callback:
                    progress_callback(progress, metrics)
                
                logger.info(
                    f"[Job {job_id}] Epoch {epoch+1}/{epochs} — "
                    f"Loss: {train_loss:.4f}, Acc: {train_acc:.1f}%, "
                    f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.1f}%"
                )
            
            # ── Step 6: Save trained model ─────────────────────
            model_id = self.registry.save_model(
                model=model,
                job_id=job_id,
                dataset_id=dataset_id,
                model_type=model_type,
                accuracy=best_accuracy,
                loss=best_loss,
                hyperparams=hyperparams
            )
            
            duration = round(time.time() - start_time, 2)
            
            result = {
                "model_id": model_id,
                "accuracy": round(best_accuracy, 2),
                "loss": round(best_loss, 4),
                "duration_seconds": duration,
                "epochs_completed": epochs
            }
            
            logger.info(f"[Job {job_id}] Training complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Training failed: {e}", exc_info=True)
            raise
            
        finally:
            # ── Step 7: SECURE CLEANUP ─────────────────────────
            # Wipe all decrypted data from memory
            logger.info(f"[Job {job_id}] Wiping decrypted data from memory...")
            
            if decrypted_buffer is not None:
                secure_wipe_buffer(decrypted_buffer)
            
            if train_data is not None:
                secure_wipe_tensor(train_data)
            if train_labels is not None:
                secure_wipe_tensor(train_labels)
            
            # Audit log for secure wipe
            execute_insert(
                """INSERT INTO audit_log (event_type, actor, details)
                   VALUES (?, ?, ?)""",
                ("MEMORY_WIPE", "sandbox", json.dumps({
                    "job_id": job_id,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            )
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"[Job {job_id}] Memory cleanup complete")

    def _evaluate(self, model, val_loader, criterion):
        """Evaluate model on validation set."""
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                total += batch_y.size(0)
                correct += predicted.eq(batch_y).sum().item()
        
        avg_loss = val_loss / max(len(val_loader), 1)
        accuracy = 100.0 * correct / max(total, 1)
        return accuracy, avg_loss
