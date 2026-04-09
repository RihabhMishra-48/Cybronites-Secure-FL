import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import os
import threading
import time
import json
import logging
import io

logger = logging.getLogger("TrainingEngine")

class TrainingSession:
    def __init__(self, code, hyperparams, bridge_broadcast_callback):
        self.code = code
        self.epochs = hyperparams.get("epochs", 5)
        self.lr = hyperparams.get("lr", 0.01)
        self.batch_size = hyperparams.get("batch_size", 32)
        self.broadcast = bridge_broadcast_callback
        self.stop_event = threading.Event()
        self.model = None
        self.status = "IDLE"
        self.progress = 0
        self.metrics = {"loss": [], "accuracy": []}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = None

    def run(self):
        try:
            self.status = "TRAINING"
            self.broadcast("LOG", f"SYSTEM: Starting training on {self.device}...")
            
            # 1. Dynamic compilation
            namespace = {}
            exec(self.code, namespace)
            
            # Look for a class that is a subclass of nn.Module
            model_class = None
            for name, obj in namespace.items():
                if isinstance(obj, type) and issubclass(obj, nn.Module) and obj is not nn.Module:
                    model_class = obj
                    break
            
            if not model_class:
                raise ValueError("No nn.Module subclass found in submitted code.")
            
            self.model = model_class().to(self.device)
            optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
            criterion = nn.Cross_entropy if hasattr(nn, 'Cross_entropy') else nn.functional.cross_entropy
            
            # 2. Data Loading
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.1307,), (0.3081,))
            ])
            train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            
            test_dataset = datasets.MNIST('./data', train=False, transform=transform)
            test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)

            # 3. Training Loop
            for epoch in range(self.epochs):
                if self.stop_event.is_set():
                    self.status = "ABORTED"
                    self.broadcast("LOG", "SYSTEM: Training aborted by user.")
                    return

                self.model.train()
                running_loss = 0.0
                for batch_idx, (data, target) in enumerate(train_loader):
                    if self.stop_event.is_set(): break
                    data, target = data.to(self.device), target.to(self.device)
                    optimizer.zero_grad()
                    output = self.model(data)
                    loss = nn.functional.cross_entropy(output, target)
                    loss.backward()
                    optimizer.step()
                    running_loss += loss.item()

                # Evaluation
                self.model.eval()
                correct = 0
                total = 0
                with torch.no_grad():
                    for data, target in test_loader:
                        data, target = data.to(self.device), target.to(self.device)
                        output = self.model(data)
                        pred = output.argmax(dim=1, keepdim=True)
                        correct += pred.eq(target.view_as(pred)).sum().item()
                        total += len(data)
                
                accuracy = correct / total
                avg_loss = running_loss / len(train_loader)
                
                self.metrics["loss"].append(avg_loss)
                self.metrics["accuracy"].append(accuracy)
                self.progress = ((epoch + 1) / self.epochs) * 100
                
                # Broadcast progress
                self.broadcast("LAB_PROGRESS", {
                    "epoch": epoch + 1,
                    "total_epochs": self.epochs,
                    "loss": avg_loss,
                    "accuracy": accuracy,
                    "progress": self.progress,
                    "status": "TRAINING"
                })
                
                logger.info(f"Epoch {epoch+1}: Loss {avg_loss:.4f}, Acc {accuracy:.4f}")

            # 4. Save results
            save_dir = os.path.join(os.getcwd(), "exports")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            timestamp = int(time.time())
            self.model_path = os.path.join(save_dir, f"model_{timestamp}.pt")
            torch.save(self.model.state_dict(), self.model_path)
            
            # Export to ONNX if possible
            onnx_path = os.path.join(save_dir, f"model_{timestamp}.onnx")
            try:
                dummy_input = torch.randn(1, 1, 28, 28).to(self.device)
                torch.onnx.export(self.model, dummy_input, onnx_path)
            except Exception as e:
                logger.warning(f"ONNX export failed: {e}")
                onnx_path = None

            self.status = "COMPLETE"
            self.broadcast("LAB_COMPLETE", {
                "status": "COMPLETE",
                "pt_path": self.model_path,
                "onnx_path": onnx_path,
                "metrics": self.metrics
            })
            self.broadcast("LOG", "SYSTEM: Training complete. Model weights exported.")

        except Exception as e:
            self.status = "ERROR"
            error_msg = f"Training Error: {str(e)}"
            logger.error(error_msg)
            self.broadcast("LAB_ERROR", {"error": error_msg})
            self.broadcast("LOG", f"FATAL: {error_msg}")

    def abort(self):
        self.stop_event.set()

# Singleton-like manager for training sessions
_current_session = None

def start_training(code, hyperparams, broadcast_callback):
    global _current_session
    if _current_session and _current_session.status == "TRAINING":
        return False, "A training session is already in progress."
    
    _current_session = TrainingSession(code, hyperparams, broadcast_callback)
    thread = threading.Thread(target=_current_session.run)
    thread.start()
    return True, "Training started."

def abort_training():
    global _current_session
    if _current_session:
        _current_session.abort()
        return True
    return False

def get_session_status():
    if _current_session:
        return {
            "status": _current_session.status,
            "progress": _current_session.progress,
            "metrics": _current_session.metrics
        }
    return {"status": "IDLE"}
