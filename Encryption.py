"""
AES Encryption Helper

Provides AES encryption and decryption helper functions used by the
Flask application and TCP socket servers.

Each encrypted value uses a new random IV so identical plaintext values do
not produce identical stored ciphertext values.
"""

import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from config import AES_KEY


class AESCipher(object):
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw):
        """Encrypt bytes and return base64 text containing IV + ciphertext."""
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CFB, iv)

        ciphertext = cipher.encrypt(raw)
        encrypted_value = iv + ciphertext

        encoded = base64.b64encode(encrypted_value)
        return encoded

    def decrypt(self, raw):
        """Decrypt base64 text containing IV + ciphertext."""
        decoded = base64.b64decode(raw)

        iv = decoded[:AES.block_size]
        ciphertext = decoded[AES.block_size:]

        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        decrypted = cipher.decrypt(ciphertext)

        return str(decrypted, "utf-8")


cipher = AESCipher(AES_KEY)