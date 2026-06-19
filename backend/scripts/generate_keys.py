#!/usr/bin/env python3
"""
Secure key generation utility for WALLET-TRUST backend.

Generates production-ready cryptographic keys:
- JWT_SECRET: For JWT token signing
- ENCRYPTION_KEY: For Fernet symmetric encryption

Usage:
    python scripts/generate_keys.py

Output:
    Displays keys in format ready to copy into .env file
    Save the output securely - these keys cannot be regenerated
"""

import os
import sys
import secrets
import base64
from cryptography.fernet import Fernet
from pathlib import Path


def generate_jwt_secret(length: int = 64) -> str:
    """
    Generate a cryptographically secure JWT secret.
    
    Args:
        length: Length of the hex string (default 64 = 32 bytes)
        
    Returns:
        Hex-encoded secret string (64 characters = 32 bytes)
    """
    # Generate 32 bytes of random data
    random_bytes = secrets.token_bytes(32)
    # Convert to hex string
    jwt_secret = random_bytes.hex()
    return jwt_secret


def generate_fernet_key() -> str:
    """
    Generate a Fernet encryption key (symmetric encryption).
    
    Fernet provides AES-128-CBC encryption with HMAC authentication.
    
    Returns:
        Base64-encoded Fernet key (suitable for ENCRYPTION_KEY)
    """
    # Fernet internally generates a 32-byte key and encodes it in base64
    key = Fernet.generate_key()
    # key is already bytes, decode to string for .env file
    return key.decode('utf-8')


def generate_private_key_entropy() -> str:
    """
    Generate entropy for Ethereum private key generation.
    
    Note: This generates random bytes that COULD be used as a private key,
    but for security reasons, you should use an Ethereum key management tool.
    
    Returns:
        Hex-encoded random bytes (64 characters = 32 bytes)
    """
    random_bytes = secrets.token_bytes(32)
    return '0x' + random_bytes.hex()


def main():
    """Generate and display cryptographic keys."""
    print("=" * 80)
    print("🔐 WALLET-TRUST KEY GENERATION UTILITY")
    print("=" * 80)
    print()
    print("⚠️  IMPORTANT SECURITY NOTICE:")
    print("   - Save these keys in a SECURE location")
    print("   - Never commit the .env file to version control")
    print("   - Use .gitignore to prevent accidental commits")
    print("   - Keys are randomly generated - they CANNOT be regenerated")
    print("   - Store backup copies in a secure vault (e.g., 1Password, LastPass)")
    print()
    print("=" * 80)
    print()
    
    # Generate JWT_SECRET
    print("1️⃣  JWT_SECRET (for token signing)")
    print("-" * 80)
    jwt_secret = generate_jwt_secret()
    print(f"JWT_SECRET={jwt_secret}")
    print()
    print("   Details:")
    print(f"   - Length: 64 characters (32 bytes)")
    print(f"   - Type: Hex-encoded random bytes")
    print(f"   - Use: JWT access token signing (HS256 algorithm)")
    print(f"   - Expiration: Tokens expire after 24 hours by default")
    print()
    
    # Generate ENCRYPTION_KEY
    print("2️⃣  ENCRYPTION_KEY (for data encryption)")
    print("-" * 80)
    encryption_key = generate_fernet_key()
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    print("   Details:")
    print(f"   - Type: Fernet symmetric encryption")
    print(f"   - Algorithm: AES-128-CBC + HMAC-SHA256")
    print(f"   - Key Length: 32 bytes (base64-encoded)")
    print(f"   - Use: Encrypt/decrypt sensitive user data")
    print()
    
    print("=" * 80)
    print("📝 NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. Create .env file in backend/ directory:")
    print("   $ cp .env.example .env")
    print()
    print("2. Update the .env file with the generated keys above:")
    print("   - Replace 'your_jwt_secret_here_minimum_32_chars' with JWT_SECRET value")
    print("   - Replace 'your_fernet_encryption_key_here' with ENCRYPTION_KEY value")
    print()
    print("3. Add blockchain configuration:")
    print("   - BLOCKCHAIN_RPC_URL: Your Ethereum RPC endpoint")
    print("   - CONTRACT_ADDRESS: Deployed contract address on Sepolia")
    print("   - PRIVATE_KEY: Your Ethereum private key (0x prefixed)")
    print()
    print("4. Verify .env is in .gitignore:")
    print("   $ grep '.env' .gitignore")
    print()
    print("5. Test configuration:")
    print("   $ cd backend && python app.py")
    print()
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()
