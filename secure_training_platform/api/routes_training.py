"""
Training API Routes — Submit training jobs and check status.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from secure_training_platform.config import SUPPORTED_MODELS
from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.training_worker.worker import submit_job, get_job_status, list_jobs
from secure_training_platform.key_manager.manager import KeyManager

router = APIRouter(prefix="/api/v1", tags=["Training"])

_vault: DatasetVault | None = None


def init_routes(vault: DatasetVault):
    global _vault
    _vault = vault


class TrainRequest(BaseModel):
    """Training job submission request."""
    dataset_id: str
    model_type: str
    epochs: int = Field(default=10, ge=1, le=100)
    batch_size: int = Field(default=32, ge=8, le=256)
    learning_rate: float = Field(default=0.001, gt=0, le=1.0)


@router.post("/train")
async def start_training(req: TrainRequest):
    """
    Submit a training job.
    
    The system will:
    1. Validate dataset and model selection
    2. Queue the job for secure processing
    3. Return a job ID for tracking
    
    The dataset is decrypted ONLY in RAM during training.
    """
    if not _vault:
        raise HTTPException(status_code=503, detail="Platform not initialized")
    
    # Validate dataset exists
    dataset_info = _vault.get_dataset_info(req.dataset_id)
    if not dataset_info:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Validate model type
    if req.model_type not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model. Choose from: {SUPPORTED_MODELS}"
        )
    
    # Check if model is allowed for this dataset
    allowed = dataset_info.get("allowed_models", [])
    if allowed and req.model_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{req.model_type}' not allowed for this dataset. "
                   f"Allowed: {allowed}"
        )
    
    # Submit to queue
    hyperparams = {
        "epochs": req.epochs,
        "batch_size": req.batch_size,
        "learning_rate": req.learning_rate
    }
    
    job_id = submit_job(req.dataset_id, req.model_type, hyperparams)
    
    return {
        "job_id": job_id,
        "status": "QUEUED",
        "message": "Training job submitted. Dataset will be decrypted in memory only.",
        "dataset": dataset_info["name"],
        "model": req.model_type,
        "hyperparameters": hyperparams
    }


@router.get("/training_status/{job_id}")
async def training_status(job_id: str):
    """Get the status and metrics of a training job."""
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/training_jobs")
async def list_training_jobs(limit: int = 50):
    """List all training jobs."""
    jobs = list_jobs(limit=limit)
    return {
        "count": len(jobs),
        "jobs": jobs
    }
