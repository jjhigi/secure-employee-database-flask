"""
Crypto Helper Functions

Provides shared encryption and decryption helpers for route modules.
"""

import Encryption


def enc(value: str) -> str:
    """Encrypt a string and return encoded text for database storage."""
    return Encryption.cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def dec(value: str) -> str:
    """Decrypt stored text back into a normal string."""
    return Encryption.cipher.decrypt(value)
