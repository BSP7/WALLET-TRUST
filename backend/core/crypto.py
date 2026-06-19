# backend/core/crypto.py
"""
Production-grade cryptography module for WALLET-TRUST.

Implements AES-256-GCM encryption instead of Fernet for better performance.
Includes secure password hashing with Argon2id.
"""

import os
import secrets
import hashlib
import hmac
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

logger = logging.getLogger(__name__)


class CryptoManager:
    """
    Secure cryptography manager for encryption and hashing operations.
    
    Uses:
    - AES-256-GCM for symmetric encryption (AEAD)
    - Argon2id for password hashing
    - HMAC-SHA256 for authentication
    """
    
    def __init__(self, master_key: str):
        """
        Initialize crypto manager with master key.
        
        Args:
            master_key: Encryption key material. Supported formats:
                - 32-byte key as 64 hex characters (AES-256)
                - Fernet/urlsafe-base64 encoded 32-byte key (common in existing .env files)
        """
        if not isinstance(master_key, str):
            raise ValueError("master_key must be a string")

        key_str = master_key.strip()
        if key_str.startswith("0x"):
            key_str = key_str[2:]

        key_bytes = None

        # Prefer hex (documented for AES-256), but accept Fernet/base64 for backward compatibility.
        try:
            candidate = bytes.fromhex(key_str)
            if len(candidate) == 32:
                key_bytes = candidate
        except ValueError:
            key_bytes = None

        if key_bytes is None:
            try:
                # Fernet keys are urlsafe base64 for 32 raw bytes.
                padded = key_str + ("=" * (-len(key_str) % 4))
                candidate = base64.urlsafe_b64decode(padded.encode("utf-8"))
                if len(candidate) != 32:
                    raise ValueError(f"Decoded key must be 32 bytes, got {len(candidate)}")
                key_bytes = candidate
            except Exception as e:
                raise ValueError(
                    "Invalid ENCRYPTION_KEY format. Expected 64 hex chars (32 bytes) "
                    "or Fernet/urlsafe-base64 encoding of 32 bytes."
                ) from e

        self.master_key = key_bytes
        
        # Initialize Argon2 password hasher
        self.hasher = PasswordHasher(
            time_cost=2,  # iterations
            memory_cost=65536,  # 64MB
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
        
        logger.info("CryptoManager initialized successfully")
    
    def encrypt_data(self, plain_data: bytes) -> str:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plain_data: Data to encrypt (bytes)
            
        Returns:
            Base64-encoded ciphertext with nonce and tag concatenated
            Format: base64(nonce || tag || ciphertext)
        """
        if not isinstance(plain_data, bytes):
            plain_data = plain_data.encode('utf-8')
        
        try:
            # Generate random 96-bit nonce (12 bytes)
            nonce = secrets.token_bytes(12)
            
            # Create cipher
            cipher = AESGCM(self.master_key)
            
            # Encrypt and authenticate
            ciphertext = cipher.encrypt(nonce, plain_data, None)
            
            # Return nonce || ciphertext (tag is included in ciphertext for GCM)
            encrypted = nonce + ciphertext
            
            # Base64 encode for storage/transmission
            encoded = base64.b64encode(encrypted).decode('utf-8')
            
            logger.debug(f"Data encrypted successfully ({len(plain_data)} bytes)")
            return encoded
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted data (bytes)
        """
        try:
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract nonce (first 12 bytes) and ciphertext (rest)
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            
            # Create cipher and decrypt
            cipher = AESGCM(self.master_key)
            plain_data = cipher.decrypt(nonce, ciphertext, None)
            
            logger.debug(f"Data decrypted successfully ({len(plain_data)} bytes)")
            return plain_data
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using Argon2id.
        
        Args:
            password: Plaintext password
            
        Returns:
            Hashed password (Argon2 PHC string format)
        """
        if not isinstance(password, str):
            password = password.decode('utf-8')
        
        try:
            hashed = self.hasher.hash(password)
            logger.debug("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash using Argon2id.
        
        Args:
            password: Plaintext password
            hashed: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        if not isinstance(password, str):
            password = password.decode('utf-8')
        
        try:
            self.hasher.verify(hashed, password)
            logger.debug("Password verified successfully")
            return True
        except (VerifyMismatchError, InvalidHashError):
            logger.warning("Password verification failed")
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure token.
        
        Args:
            length: Token length in bytes (default 32 = 256 bits)
            
        Returns:
            Hex-encoded random token
        """
        token = secrets.token_hex(length)
        logger.debug(f"Token generated ({length} bytes)")
        return token
    
    def generate_salt(self, length: int = 16) -> str:
        """
        Generate a random salt for password hashing.
        
        Args:
            length: Salt length in bytes (default 16)
            
        Returns:
            Hex-encoded random salt
        """
        return secrets.token_hex(length)
    
    def hash_password_with_salt(self, password: str, salt: str) -> str:
        """
        Hash password with a provided salt using SHA-256.
        
        Args:
            password: Plaintext password
            salt: Hex-encoded salt
            
        Returns:
            Hex-encoded hash
        """
        if not isinstance(password, str):
            password = password.decode('utf-8')
        
        # Combine password and salt
        salted = (password + salt).encode('utf-8')
        hashed = hashlib.sha256(salted).hexdigest()
        logger.debug("Password hashed with salt successfully")
        return hashed
    
    def verify_password_with_salt(self, password: str, hashed: str, salt: str) -> bool:
        """
        Verify password against hash using salt.
        
        Args:
            password: Plaintext password
            hashed: Hashed password from database
            salt: Hex-encoded salt
            
        Returns:
            True if password matches, False otherwise
        """
        computed_hash = self.hash_password_with_salt(password, salt)
        return hmac.compare_digest(computed_hash, hashed)
    
    def generate_key() -> str:
        """
        Generate a new AES-256 master key.
        
        Returns:
            32-byte key as hex string
        """
        key = secrets.token_bytes(32)
        key_hex = key.hex()
        logger.info("New encryption key generated")
        return key_hex


class SecureHash:
    """Helper class for secure hashing operations."""
    
    @staticmethod
    def sha256(data: bytes) -> str:
        """
        Generate SHA-256 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def hmac_sha256(data: bytes, key: bytes) -> str:
        """
        Generate HMAC-SHA256.
        
        Args:
            data: Data to authenticate
            key: Authentication key
            
        Returns:
            Hex-encoded HMAC
        """
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def pbkdf2(password: str, salt: bytes, iterations: int = 600000) -> str:
        """
        Derive key using PBKDF2 (for backward compatibility).
        
        NOTE: This is deprecated. Use Argon2id instead via hash_password().
        
        Args:
            password: Password to derive from
            salt: Salt bytes
            iterations: Number of iterations
            
        Returns:
            Derived key as hex string
        """
        # Use PBKDF2 from hashlib for backward compatibility
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
        return key.hex()


class TokenValidator:
    """Validate security tokens and signatures."""
    
    @staticmethod
    def is_valid_jwt_format(token: str) -> bool:
        """Validate JWT format (3 parts separated by dots)."""
        parts = token.split('.')
        return len(parts) == 3 and all(p for p in parts)
    
    @staticmethod
    def is_valid_hex_string(data: str, expected_length: int = None) -> bool:
        """Validate hex string format."""
        if not isinstance(data, str):
            return False
        try:
            bytes.fromhex(data)
            if expected_length and len(bytes.fromhex(data)) != expected_length:
                return False
            return True
        except ValueError:
            return False
