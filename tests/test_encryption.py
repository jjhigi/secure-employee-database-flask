import Encryption


def test_encrypt_round_trip_uses_fresh_ciphertext():
    plaintext = "sensitive employee field"

    first_ciphertext = Encryption.cipher.encrypt(plaintext.encode("utf-8"))
    second_ciphertext = Encryption.cipher.encrypt(plaintext.encode("utf-8"))

    assert Encryption.cipher.decrypt(first_ciphertext) == plaintext
    assert Encryption.cipher.decrypt(second_ciphertext) == plaintext
    assert first_ciphertext != second_ciphertext
