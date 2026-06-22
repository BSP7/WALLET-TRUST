import pytest
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from core.crypto import CryptoManager

def test_crypto_manager_initialization():
    # Valid hex key (32 bytes = 64 hex chars)
    hex_key = os.urandom(32).hex()
    cm = CryptoManager(master_key=hex_key)
    assert len(cm.master_key) == 32

    # Valid Fernet key (urlsafe base64 of 32 bytes)
    fernet_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    cm_fernet = CryptoManager(master_key=fernet_key)
    assert len(cm_fernet.master_key) == 32

    # Invalid string length
    with pytest.raises(ValueError):
        CryptoManager(master_key="invalid_short_key")

def test_encrypt_decrypt_symmetric():
    hex_key = os.urandom(32).hex()
    cm = CryptoManager(master_key=hex_key)
    
    plaintext = b"sensitive payload data"
    encrypted = cm.encrypt_data(plaintext)
    
    # Assert return type is base64 string
    assert isinstance(encrypted, str)
    assert encrypted != plaintext.decode('utf-8')

    decrypted = cm.decrypt_data(encrypted)
    assert decrypted == plaintext

def test_encrypt_decrypt_string():
    hex_key = os.urandom(32).hex()
    cm = CryptoManager(master_key=hex_key)
    
    plaintext_str = "sensitive payload string"
    encrypted = cm.encrypt_data(plaintext_str)
    
    decrypted = cm.decrypt_data(encrypted)
    assert decrypted.decode('utf-8') == plaintext_str

def test_invalid_key_decryption():
    hex_key_1 = os.urandom(32).hex()
    cm_1 = CryptoManager(master_key=hex_key_1)
    
    hex_key_2 = os.urandom(32).hex()
    cm_2 = CryptoManager(master_key=hex_key_2)
    
    plaintext = b"secret data"
    encrypted = cm_1.encrypt_data(plaintext)
    
    # Decrypting with wrong key should fail
    with pytest.raises(Exception):
        cm_2.decrypt_data(encrypted)

def test_tampered_ciphertext():
    hex_key = os.urandom(32).hex()
    cm = CryptoManager(master_key=hex_key)
    
    encrypted = cm.encrypt_data(b"secret data")
    raw_bytes = base64.b64decode(encrypted.encode('utf-8'))
    
    # Tamper with the ciphertext (flip a bit in the last byte)
    tampered_bytes = bytearray(raw_bytes)
    tampered_bytes[-1] ^= 0x01
    tampered_b64 = base64.b64encode(tampered_bytes).decode('utf-8')
    
    # Should raise cryptography exception (Authentication tag mismatch)
    with pytest.raises(Exception):
        cm.decrypt_data(tampered_b64)

def test_invalid_nonce():
    hex_key = os.urandom(32).hex()
    cm = CryptoManager(master_key=hex_key)
    
    encrypted = cm.encrypt_data(b"secret data")
    raw_bytes = base64.b64decode(encrypted.encode('utf-8'))
    
    # Tamper with the nonce (first 12 bytes)
    tampered_bytes = bytearray(raw_bytes)
    tampered_bytes[0] ^= 0x01
    tampered_b64 = base64.b64encode(tampered_bytes).decode('utf-8')
    
    with pytest.raises(Exception):
        cm.decrypt_data(tampered_b64)
