"""
AES Encryption Helper

Provides AES encryption and decryption helpers used by the Flask application
and local TCP socket servers.

Each encrypted value uses a new random IV so identical plaintext values do not
produce identical stored ciphertext values.
"""

import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from config import AES_KEY


class AESCipher:
    """AES-CFB helper that stores each encrypted value as base64 IV + ciphertext."""

    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext_bytes):
        """Encrypt bytes and return base64-encoded IV + ciphertext bytes."""
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CFB, iv)

        ciphertext = cipher.encrypt(plaintext_bytes)
        encrypted_value = iv + ciphertext

        return base64.b64encode(encrypted_value)

    def decrypt(self, encrypted_text):
        """Decrypt base64-encoded IV + ciphertext into a normal string."""
        decoded = base64.b64decode(encrypted_text)

        iv = decoded[:AES.block_size]
        ciphertext = decoded[AES.block_size:]

        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        decrypted = cipher.decrypt(ciphertext)

        return decrypted.decode("utf-8")


cipher = AESCipher(AES_KEY)