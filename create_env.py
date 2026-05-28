"""
Local Environment File Generator

Creates a local .env file with generated secrets if one does not already exist.
"""

import secrets
import string
from pathlib import Path

ENV_FILE = Path(".env")
AES_KEY_LENGTH = 32


def generate_aes_key() -> str:
    """Return a 32-character ASCII AES key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(AES_KEY_LENGTH))


def create_env_file() -> None:
    """Create .env with generated local secrets unless it already exists."""
    if ENV_FILE.exists():
        print(".env already exists. Keeping existing local configuration.")
        return

    flask_secret = secrets.token_urlsafe(32)
    hmac_secret = secrets.token_urlsafe(32)
    aes_key = generate_aes_key()

    ENV_FILE.write_text(
        "\n".join(
            [
                "FLASK_SECRET_KEY=" + flask_secret,
                "FLASK_DEBUG=0",
                "HMAC_SECRET=" + hmac_secret,
                "AES_KEY=" + aes_key,
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(".env created with generated local secrets.")


if __name__ == "__main__":
    create_env_file()