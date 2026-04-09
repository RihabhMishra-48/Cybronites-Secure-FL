"""
Secure AI Training Platform — FastAPI Application Entry Point.

Initializes all services and starts the API server with background training worker.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from secure_training_platform.config import API_HOST, API_PORT, LOG_LEVEL
from secure_training_platform.database.db import init_db
from secure_training_platform.key_manager.manager import KeyManager
from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.model_registry.registry import ModelRegistry
from secure_training_platform.training_worker.worker import TrainingWorker

from secure_training_platform.api import routes_datasets, routes_models, routes_training
from secure_training_platform.api.middleware import (
    RequestLoggingMiddleware, APIKeyMiddleware, RateLimitMiddleware
)

# ── Logging Setup ──────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Service Instances ──────────────────────────────────────
key_manager = KeyManager()
vault = DatasetVault(key_manager)
registry = ModelRegistry()
worker = TrainingWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    logger.info("═" * 60)
    logger.info("  Secure AI Training Platform — Starting")
    logger.info("═" * 60)
    
    init_db()
    worker.start()
    
    logger.info(f"API server ready on http://{API_HOST}:{API_PORT}")
    logger.info("Training worker active — listening for jobs")
    logger.info("═" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down training worker...")
    worker.stop()
    logger.info("Platform shutdown complete")


# ── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="Secure AI Training Platform",
    description=(
        "Privacy-first ML training platform. Datasets remain encrypted at rest "
        "and are decrypted only in RAM during training. Users train models "
        "without ever accessing raw data."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── Middleware ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
# API key auth is optional in dev; enable for production:
# app.add_middleware(APIKeyMiddleware)

# ── Initialize Routes ─────────────────────────────────────
routes_datasets.init_routes(vault)
routes_models.init_routes(registry)
routes_training.init_routes(vault)

app.include_router(routes_datasets.router)
app.include_router(routes_models.router)
app.include_router(routes_training.router)


# ── Health Check ───────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "platform": "Secure AI Training Platform",
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "key_manager": "ok",
            "dataset_vault": "ok",
            "model_registry": "ok",
            "training_worker": "active"
        }
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Secure AI Training Platform",
        "description": "Privacy-first ML training — datasets never exposed",
        "docs": "/docs",
        "endpoints": {
            "datasets": "/api/v1/datasets",
            "models": "/api/v1/models",
            "train": "/api/v1/train",
            "status": "/api/v1/training_status/{job_id}",
            "jobs": "/api/v1/training_jobs"
        }
    }


# ── CLI Entry Point ───────────────────────────────────────
def run():
    """Run the server directly."""
    import uvicorn
    uvicorn.run(
        "secure_training_platform.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    run()
