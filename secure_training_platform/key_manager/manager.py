"""
Key Manager — Secure storage and access control for encryption keys.

Keys are double-encrypted: dataset AES keys are encrypted with a master key
before being stored in the database. Only authorized roles can retrieve keys.
"""
from __future__ import annotations

import os
import uuid
import json
import logging
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from secure_training_platform.config import MASTER_KEY_ENV, AES_KEY_LENGTH
from secure_training_platform.database.db import execute_query, execute_insert

logger = logging.getLogger(__name__)

# Roles allowed to retrieve decryption keys
AUTHORIZED_ROLES = {"training_worker", "system"}


class KeyManager:
    """
    Manages encryption keys with double-encryption and strict access control.
    
    Security properties:
    - Keys stored encrypted with a master key (never plaintext on disk)
    - Only 'training_worker' and 'system' roles can retrieve keys
    - Every key access is logged to the audit table
    """

    def __init__(self):
        self._master_key = self._load_master_key()
        logger.info("Key Manager initialized")

    def _load_master_key(self) -> bytes:
        """
        Load or derive the master key.
        In production, this should come from an HSM or cloud KMS.
        """
        if MASTER_KEY_ENV:
            # Derive a 256-bit key from the env variable
            return hashlib.sha256(MASTER_KEY_ENV.encode()).digest()
        
        # Development fallback: derive from a fixed seed + machine identity
        # ⚠️ Replace with proper KMS in production
        seed = f"stp-dev-master-{os.getenv('USER', 'default')}"
        key = hashlib.sha256(seed.encode()).digest()
        logger.warning("Using development master key — NOT FOR PRODUCTION")
        return key

    def store_key(self, dataset_id: str, raw_key: bytes, key_id: str | None = None) -> str:
        """
        Encrypt a dataset key with the master key and store it.
        
        Returns:
            key_id for referencing this key.
        """
        if key_id is None:
            key_id = str(uuid.uuid4())

        # Encrypt the dataset key with master key
        aesgcm = AESGCM(self._master_key)
        nonce = os.urandom(12)
        encrypted_key = aesgcm.encrypt(nonce, raw_key, None)

        # Store encrypted key + nonce + tag
        # Note: AESGCM.encrypt appends the 16-byte tag to ciphertext
        # We store: encrypted_key (includes tag), nonce separately
        execute_insert(
            """INSERT INTO encryption_keys 
               (key_id, dataset_id, encrypted_key, key_nonce, key_tag)
               VALUES (?, ?, ?, ?, ?)""",
            (key_id, dataset_id, encrypted_key, nonce, b"gcm_integrated")
        )

        self._log_audit("KEY_STORE", {
            "key_id": key_id,
            "dataset_id": dataset_id,
            "action": "stored_encrypted_key"
        })

        logger.info(f"Stored encrypted key {key_id} for dataset {dataset_id}")
        return key_id

    def retrieve_key(self, key_id: str, requester_role: str = "unknown") -> bytes:
        """
        Retrieve and decrypt a dataset key.
        
        Access control: Only AUTHORIZED_ROLES can retrieve keys.
        Every access is logged for audit.
        
        Returns:
            Raw AES-256 decryption key (caller must wipe after use).
        
        Raises:
            PermissionError if requester_role is not authorized.
            KeyError if key_id not found.
        """
        # Access control check
        if requester_role not in AUTHORIZED_ROLES:
            self._log_audit("KEY_ACCESS_DENIED", {
                "key_id": key_id,
                "requester_role": requester_role,
                "reason": "unauthorized_role"
            })
            logger.warning(f"KEY ACCESS DENIED: role={requester_role}, key={key_id}")
            raise PermissionError(
                f"Role '{requester_role}' is not authorized to access encryption keys"
            )

        # Retrieve encrypted key from DB
        rows = execute_query(
            "SELECT encrypted_key, key_nonce FROM encryption_keys WHERE key_id = ?",
            (key_id,)
        )
        if not rows:
            raise KeyError(f"Encryption key {key_id} not found")

        encrypted_key = rows[0]["encrypted_key"]
        nonce = rows[0]["key_nonce"]

        # Ensure bytes type (sqlite may return memoryview)
        if not isinstance(encrypted_key, bytes):
            encrypted_key = bytes(encrypted_key)
        if not isinstance(nonce, bytes):
            nonce = bytes(nonce)

        # Decrypt with master key
        aesgcm = AESGCM(self._master_key)
        raw_key = aesgcm.decrypt(nonce, encrypted_key, None)

        # Update last_accessed timestamp
        execute_insert(
            "UPDATE encryption_keys SET last_accessed = ? WHERE key_id = ?",
            (datetime.utcnow().isoformat(), key_id)
        )

        # Audit log
        self._log_audit("KEY_ACCESS", {
            "key_id": key_id,
            "requester_role": requester_role,
            "action": "key_retrieved"
        })

        logger.info(f"Key {key_id} retrieved by role={requester_role}")
        return raw_key

    def _log_audit(self, event_type: str, details: dict):
        """Write an entry to the audit log."""
        try:
            execute_insert(
                """INSERT INTO audit_log (event_type, actor, details)
                   VALUES (?, ?, ?)""",
                (event_type, details.get("requester_role", "system"), json.dumps(details))
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def list_keys_for_dataset(self, dataset_id: str) -> list[dict]:
        """List key metadata for a dataset (no raw keys exposed)."""
        return execute_query(
            """SELECT key_id, dataset_id, created_at, last_accessed 
               FROM encryption_keys WHERE dataset_id = ?""",
            (dataset_id,)
        )
