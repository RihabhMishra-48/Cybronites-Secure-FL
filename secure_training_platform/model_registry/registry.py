"""
Model Registry — Stores and manages trained model artifacts.
Users can list and download models but cannot access source datasets.
"""
from __future__ import annotations

import os
import uuid
import json
import logging
from pathlib import Path

import torch

from secure_training_platform.config import MODEL_REGISTRY_DIR
from secure_training_platform.database.db import execute_query, execute_insert

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages trained model storage and metadata."""

    def __init__(self):
        self.models_dir = MODEL_REGISTRY_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def save_model(self, model, job_id: str, dataset_id: str,
                   model_type: str, accuracy: float, loss: float,
                   hyperparams: dict) -> str:
        """
        Save a trained model and register metadata.
        
        Returns:
            model_id
        """
        model_id = str(uuid.uuid4())
        filename = f"{model_id}.pt"
        file_path = self.models_dir / filename
        
        # Save model state dict
        torch.save(model.state_dict(), file_path)
        file_size = file_path.stat().st_size
        
        # Register in database
        execute_insert(
            """INSERT INTO trained_models 
               (id, job_id, dataset_id, model_type, file_path,
                accuracy, loss, hyperparameters, file_size)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model_id, job_id, dataset_id, model_type,
                str(file_path), accuracy, loss,
                json.dumps(hyperparams), file_size
            )
        )
        
        logger.info(
            f"Saved model {model_id} ({model_type}, "
            f"acc={accuracy:.1f}%, size={file_size} bytes)"
        )
        return model_id

    def list_models(self) -> list[dict]:
        """List all trained models with metadata."""
        rows = execute_query(
            """SELECT m.id, m.job_id, m.dataset_id, m.model_type,
                      m.accuracy, m.loss, m.hyperparameters, 
                      m.file_size, m.created_at,
                      d.name as dataset_name
               FROM trained_models m
               LEFT JOIN datasets d ON m.dataset_id = d.id
               ORDER BY m.created_at DESC"""
        )
        for row in rows:
            row["hyperparameters"] = json.loads(row.get("hyperparameters", "{}"))
        return rows

    def get_model(self, model_id: str) -> dict | None:
        """Get model metadata by ID."""
        rows = execute_query(
            """SELECT m.*, d.name as dataset_name
               FROM trained_models m
               LEFT JOIN datasets d ON m.dataset_id = d.id
               WHERE m.id = ?""",
            (model_id,)
        )
        if not rows:
            return None
        row = rows[0]
        row["hyperparameters"] = json.loads(row.get("hyperparameters", "{}"))
        return row

    def get_model_file_path(self, model_id: str) -> Path | None:
        """Get the file path for downloading a trained model."""
        rows = execute_query(
            "SELECT file_path FROM trained_models WHERE id = ?",
            (model_id,)
        )
        if not rows:
            return None
        path = Path(rows[0]["file_path"])
        return path if path.exists() else None

    def delete_model(self, model_id: str) -> bool:
        """Delete a model file and its metadata."""
        path = self.get_model_file_path(model_id)
        if path and path.exists():
            path.unlink()
        
        execute_insert(
            "DELETE FROM trained_models WHERE id = ?",
            (model_id,)
        )
        logger.info(f"Deleted model {model_id}")
        return True
