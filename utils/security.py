"""Basic password hashing helpers for the local desktop application."""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash suitable for local credential storage."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Safely compare a plaintext password with a stored password hash."""
    try:
        salt_hex, expected_hash = stored_hash.split(":", maxsplit=1)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 100_000
        )
        return hmac.compare_digest(digest.hex(), expected_hash)
    except (ValueError, AttributeError):
        return False
