"""
Dataset API Routes — List available datasets (metadata only, no raw data).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.key_manager.manager import KeyManager

router = APIRouter(prefix="/api/v1", tags=["Datasets"])

# Lazy-initialized references (set by main.py)
_vault: DatasetVault | None = None


def init_routes(vault: DatasetVault):
    global _vault
    _vault = vault


@router.get("/datasets")
async def list_datasets():
    """
    List all available datasets with metadata.
    No file paths or encryption keys are exposed.
    """
    if not _vault:
        raise HTTPException(status_code=503, detail="Vault not initialized")
    
    datasets = _vault.list_datasets()
    return {
        "count": len(datasets),
        "datasets": datasets
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get metadata for a specific dataset."""
    if not _vault:
        raise HTTPException(status_code=503, detail="Vault not initialized")
    
    info = _vault.get_dataset_info(dataset_id)
    if not info:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Remove sensitive fields before returning
    safe_info = {k: v for k, v in info.items() 
                 if k not in ("encrypted_file_path", "encryption_key_id")}
    return safe_info
