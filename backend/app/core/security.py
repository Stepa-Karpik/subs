from __future__ import annotations

import base64
import hashlib
import hmac
from cryptography.fernet import Fernet


def _fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_text(value: str | None, secret: str) -> str | None:
    if not value:
        return None
    return Fernet(_fernet_key(secret)).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str | None, secret: str) -> str | None:
    if not value:
        return None
    try:
        return Fernet(_fernet_key(secret)).decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def hash_identifier(value: str | None, pepper: str) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return hmac.new(pepper.encode("utf-8"), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_identifier(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if "@" in value:
        name, domain = value.split("@", 1)
        prefix = name[:1] + "***" if name else "***"
        return f"{prefix}@{domain}"
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"
