"""
Secure AI Training Platform — Central Configuration
All settings configurable via environment variables.
"""

import os
from pathlib import Path

# ── Base Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATASET_VAULT_DIR = BASE_DIR / "dataset_vault" / "datasets"
MODEL_REGISTRY_DIR = BASE_DIR / "model_registry" / "models"
DATABASE_PATH = BASE_DIR / "database" / "secure_platform.db"

# Ensure directories exist
DATASET_VAULT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Security ────────────────────────────────────────────────
# Master key for encrypting dataset decryption keys (double encryption)
# In production: load from HSM / Vault / KMS — never hardcode
MASTER_KEY_ENV = os.getenv("STP_MASTER_KEY", None)

# AES-256 key length in bytes
AES_KEY_LENGTH = 32

# ── Redis (Job Queue) ──────────────────────────────────────
REDIS_HOST = os.getenv("STP_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("STP_REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("STP_REDIS_DB", "0"))
REDIS_QUEUE_NAME = "secure_training_jobs"

# ── Training Defaults ──────────────────────────────────────
DEFAULT_EPOCHS = 10
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
MAX_CONCURRENT_JOBS = int(os.getenv("STP_MAX_JOBS", "2"))

# ── API ─────────────────────────────────────────────────────
API_HOST = os.getenv("STP_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("STP_API_PORT", "8100"))
API_KEY = os.getenv("STP_API_KEY", "dev-api-key-change-in-prod")

# ── Supported Models ───────────────────────────────────────
SUPPORTED_MODELS = ["SimpleCNN", "ResNet18", "MLP"]

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL = os.getenv("STP_LOG_LEVEL", "INFO")
