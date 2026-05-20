"""
Crypto Helper Functions

Provides shared encryption and decryption helpers for route modules.
"""

import Encryption


def enc(s: str) -> str:
    """Encrypt a Python string and return text."""
    return Encryption.cipher.encrypt(s.encode("utf-8")).decode("utf-8")


def dec(s: str) -> str:
    """Decrypt text from the database back into a normal string."""
    return Encryption.cipher.decrypt(s)