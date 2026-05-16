"""
AES Encryption Helper

Provides AES encryption and decryption helper functions used by the
Flask application and TCP socket servers.
"""

import base64

from Crypto.Cipher import AES

from config import AES_KEY, AES_IV


class AESCipher(object):
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv

    def encrypt(self, raw):
        self.cipher = AES.new(self.key, AES.MODE_CFB, self.iv)
        ciphertext = self.cipher.encrypt(raw)
        encoded = base64.b64encode(ciphertext)
        return encoded

    def decrypt(self, raw):
        decoded = base64.b64decode(raw)
        self.cipher = AES.new(self.key, AES.MODE_CFB, self.iv)
        decrypted = self.cipher.decrypt(decoded)
        return str(decrypted, "utf-8")


cipher = AESCipher(AES_KEY, AES_IV)