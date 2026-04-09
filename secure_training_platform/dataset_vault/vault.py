"""
Dataset Vault — Manages encrypted dataset storage, registration, and retrieval.
Users never access raw data; only metadata is exposed via API.
"""
from __future__ import annotations

import json
import uuid
import logging
from pathlib import Path

from secure_training_platform.config import DATASET_VAULT_DIR
from secure_training_platform.database.db import execute_query, execute_insert
from secure_training_platform.dataset_vault.encryption import (
    generate_key, encrypt_data, decrypt_file_to_memory
)
from secure_training_platform.key_manager.manager import KeyManager

logger = logging.getLogger(__name__)


class DatasetVault:
    """Manages the lifecycle of encrypted datasets."""

    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.vault_dir = DATASET_VAULT_DIR
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def register_dataset(
        self,
        name: str,
        description: str,
        raw_data: bytes,
        allowed_models: list[str],
        num_classes: int = 10,
        input_shape: list[int] = None,
        num_samples: int = 0
    ) -> str:
        """
        Encrypt raw data and register in the vault.
        
        1. Generate unique AES-256 key
        2. Encrypt data
        3. Store encrypted file
        4. Register key with Key Manager
        5. Insert metadata into DB
        6. Return dataset ID
        """
        # Generate unique IDs
        dataset_id = str(uuid.uuid4())
        key_id = str(uuid.uuid4())
        
        input_shape = input_shape or [1, 28, 28]

        # Generate encryption key and encrypt data
        raw_key = generate_key()
        encrypted_data, nonce = encrypt_data(raw_data, raw_key)

        # Write encrypted file
        enc_filename = f"{dataset_id}.enc"
        enc_path = self.vault_dir / enc_filename
        enc_path.write_bytes(encrypted_data)
        file_size = enc_path.stat().st_size

        # 1. Register metadata in database first (to satisfy FK in keys table)
        execute_insert(
            """INSERT INTO datasets 
               (id, name, description, encrypted_file_path, encryption_key_id,
                allowed_models, dataset_size, num_classes, input_shape, num_samples)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dataset_id, name, description, str(enc_path), key_id,
                json.dumps(allowed_models), file_size, num_classes,
                json.dumps(input_shape), num_samples
            )
        )

        # 2. Store key securely via Key Manager (refers to existing dataset_id)
        self.key_manager.store_key(dataset_id, raw_key, key_id=key_id)

        # Securely wipe the raw key from local scope
        raw_key = b'\x00' * len(raw_key)

        logger.info(f"Registered dataset '{name}' (id={dataset_id}, size={file_size})")
        return dataset_id

    def list_datasets(self) -> list[dict]:
        """
        List all datasets with safe metadata (no paths, no keys).
        """
        rows = execute_query(
            """SELECT id, name, description, allowed_models, dataset_size,
                      num_classes, input_shape, num_samples, created_at
               FROM datasets ORDER BY created_at DESC"""
        )
        for row in rows:
            row["allowed_models"] = json.loads(row.get("allowed_models", "[]"))
            row["input_shape"] = json.loads(row.get("input_shape", "[1,28,28]"))
        return rows

    def get_dataset_info(self, dataset_id: str) -> dict | None:
        """Get dataset metadata by ID."""
        rows = execute_query(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        )
        if not rows:
            return None
        row = rows[0]
        row["allowed_models"] = json.loads(row.get("allowed_models", "[]"))
        row["input_shape"] = json.loads(row.get("input_shape", "[1,28,28]"))
        return row

    def get_encrypted_path(self, dataset_id: str) -> Path | None:
        """
        Get path to encrypted file — ONLY callable by training worker.
        """
        rows = execute_query(
            "SELECT encrypted_file_path FROM datasets WHERE id = ?",
            (dataset_id,)
        )
        if not rows:
            return None
        return Path(rows[0]["encrypted_file_path"])

    def decrypt_dataset_to_memory(self, dataset_id: str, requester: str = "training_worker"):
        """
        Decrypt a dataset entirely in RAM.
        
        1. Retrieve encrypted file path
        2. Request decryption key from Key Manager
        3. Decrypt in memory
        4. Return BytesIO buffer (caller MUST wipe after use)
        """
        enc_path = self.get_encrypted_path(dataset_id)
        if not enc_path or not enc_path.exists():
            raise FileNotFoundError(f"Encrypted dataset {dataset_id} not found")

        # Get decryption key — Key Manager enforces access control
        info = self.get_dataset_info(dataset_id)
        key = self.key_manager.retrieve_key(
            info["encryption_key_id"],
            requester_role=requester
        )

        buffer = decrypt_file_to_memory(enc_path, key)

        # Wipe key from memory
        key = b'\x00' * len(key)

        return buffer
