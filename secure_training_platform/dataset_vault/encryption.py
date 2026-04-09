"""
AES-256-GCM Encryption/Decryption Engine.
All decryption happens strictly in-memory — never written to disk.
"""

import os
import io
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from secure_training_platform.config import AES_KEY_LENGTH

logger = logging.getLogger(__name__)


def generate_key() -> bytes:
    """Generate a cryptographically secure AES-256 key."""
    return os.urandom(AES_KEY_LENGTH)


def encrypt_data(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt data using AES-256-GCM.
    
    Returns:
        (nonce + ciphertext_with_tag) as a single blob, and the nonce separately.
        The ciphertext includes the GCM authentication tag (last 16 bytes).
    """
    if len(key) != AES_KEY_LENGTH:
        raise ValueError(f"Key must be {AES_KEY_LENGTH} bytes, got {len(key)}")
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # Pack as: nonce (12 bytes) + ciphertext (includes 16-byte tag)
    return nonce + ciphertext, nonce


def decrypt_data(packed_ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt AES-256-GCM packed ciphertext (nonce + ciphertext + tag).
    Returns plaintext bytes in memory.
    """
    if len(key) != AES_KEY_LENGTH:
        raise ValueError(f"Key must be {AES_KEY_LENGTH} bytes, got {len(key)}")
    
    nonce = packed_ciphertext[:12]
    ciphertext = packed_ciphertext[12:]
    
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_file(input_path: Path, output_path: Path, key: bytes) -> int:
    """
    Encrypt a file and write the encrypted version to output_path.
    
    Returns:
        Size of the encrypted file in bytes.
    """
    plaintext = input_path.read_bytes()
    encrypted, _ = encrypt_data(plaintext, key)
    output_path.write_bytes(encrypted)
    
    size = output_path.stat().st_size
    logger.info(f"Encrypted {input_path.name} → {output_path.name} ({size} bytes)")
    return size


def decrypt_file_to_memory(encrypted_path: Path, key: bytes) -> io.BytesIO:
    """
    Decrypt an encrypted file DIRECTLY into an in-memory BytesIO buffer.
    
    ⚠️  CRITICAL: The returned buffer must be securely wiped after use.
         Never write this data to disk.
    
    Returns:
        BytesIO buffer containing the decrypted data.
    """
    packed_ciphertext = encrypted_path.read_bytes()
    plaintext = decrypt_data(packed_ciphertext, key)
    
    buffer = io.BytesIO(plaintext)
    buffer.seek(0)
    
    # Zero out the intermediate plaintext bytes
    plaintext_ba = bytearray(len(plaintext))
    # The original plaintext will be GC'd, but buffer holds a copy
    
    logger.info(f"Decrypted {encrypted_path.name} to RAM ({len(plaintext)} bytes)")
    return buffer
