"""
Model API Routes — List and download trained models.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from secure_training_platform.model_registry.registry import ModelRegistry

router = APIRouter(prefix="/api/v1", tags=["Models"])

_registry: ModelRegistry | None = None


def init_routes(registry: ModelRegistry):
    global _registry
    _registry = registry


@router.get("/models")
async def list_models():
    """List all trained models with metadata."""
    if not _registry:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    
    models = _registry.list_models()
    # Strip file paths from response
    for m in models:
        m.pop("file_path", None)
    
    return {
        "count": len(models),
        "models": models
    }


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get metadata for a specific trained model."""
    if not _registry:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    
    model = _registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model.pop("file_path", None)
    return model


@router.get("/models/{model_id}/download")
async def download_model(model_id: str):
    """
    Download a trained model file (.pt).
    Users can download models but cannot access source datasets.
    """
    if not _registry:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    
    path = _registry.get_model_file_path(model_id)
    if not path:
        raise HTTPException(status_code=404, detail="Model file not found")
    
    return FileResponse(
        path=str(path),
        filename=f"model_{model_id}.pt",
        media_type="application/octet-stream"
    )
