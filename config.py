"""
Application Configuration

Loads local configuration values from environment variables or a local .env file.
The real .env file should not be committed to GitHub.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear setup error."""
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Create a .env file using .env.example as a template."
        )

    return value


def get_required_env_bytes(name: str) -> bytes:
    """Return a required environment variable encoded as UTF-8 bytes."""
    return get_required_env(name).encode("utf-8")


FLASK_SECRET_KEY = get_required_env("FLASK_SECRET_KEY")
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

HMAC_SECRET = get_required_env_bytes("HMAC_SECRET")
AES_KEY = get_required_env_bytes("AES_KEY")

if len(AES_KEY) not in (16, 24, 32):
    raise RuntimeError(
        "AES_KEY must be 16, 24, or 32 characters long after UTF-8 encoding."
    )