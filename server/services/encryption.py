"""
Token Encryption Service
=========================

Encrypts and decrypts sensitive tokens (GitHub PAT, Agent Zero API tokens).
Uses Fernet symmetric encryption with a key stored in environment or auto-generated.
"""

import logging
import os
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Encryption key location
ENCRYPTION_KEY_FILE = Path.home() / ".seaforge" / "encryption.key"


def _get_or_create_encryption_key() -> bytes:
    """
    Get encryption key from environment or file, or create new one.
    
    Priority:
    1. Environment variable SEAFORGE_ENCRYPTION_KEY
    2. File at ~/.seaforge/encryption.key
    3. Generate new key and save to file
    
    Returns:
        Encryption key bytes
    """
    # Check environment variable
    env_key = os.getenv("SEAFORGE_ENCRYPTION_KEY")
    if env_key:
        logger.info("Using encryption key from environment variable")
        return env_key.encode()
    
    # Check file
    if ENCRYPTION_KEY_FILE.exists():
        logger.info(f"Using encryption key from {ENCRYPTION_KEY_FILE}")
        return ENCRYPTION_KEY_FILE.read_bytes()
    
    # Generate new key
    logger.info(f"Generating new encryption key and saving to {ENCRYPTION_KEY_FILE}")
    key = Fernet.generate_key()
    
    # Ensure directory exists
    ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save key
    ENCRYPTION_KEY_FILE.write_bytes(key)
    
    # Set restrictive permissions (owner read/write only)
    ENCRYPTION_KEY_FILE.chmod(0o600)
    
    return key


# Initialize Fernet cipher
_encryption_key = _get_or_create_encryption_key()
_cipher = Fernet(_encryption_key)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token.
    
    Args:
        token: Plain text token
    
    Returns:
        Encrypted token (base64 encoded)
    """
    if not token:
        return ""
    
    encrypted = _cipher.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token.
    
    Args:
        encrypted_token: Encrypted token (base64 encoded)
    
    Returns:
        Plain text token
    """
    if not encrypted_token:
        return ""
    
    try:
        decrypted = _cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt token: {e}")
        raise ValueError("Invalid or corrupted encrypted token")


def is_encrypted(token: str) -> bool:
    """
    Check if a token appears to be encrypted.
    
    Args:
        token: Token to check
    
    Returns:
        True if token appears encrypted
    """
    if not token:
        return False
    
    # Fernet tokens are base64 encoded and start with 'gAAAAA'
    try:
        return token.startswith("gAAAAA")
    except:
        return False
