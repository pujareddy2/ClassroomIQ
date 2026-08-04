from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load env values from project root or backend root so auth and DB share
# the same configuration source regardless of current working directory.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[3]  # ClassroomIQ/
_BACKEND_ROOT = _HERE.parents[2]  # ClassroomIQ/backend/

_dotenv_path = _PROJECT_ROOT / ".env"
if not _dotenv_path.exists():
    _dotenv_path = _BACKEND_ROOT / ".env"

load_dotenv(dotenv_path=str(_dotenv_path))

# Use PBKDF2-SHA256 for stable password hashing without bcrypt's 72-byte
# input limitation.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
logger = logging.getLogger(__name__)
_FALLBACK_SECRET = "classroomiq-dev-secret-change-me"


def _get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key:
        logger.warning(
            "SECRET_KEY not set. Using development fallback secret. "
            "Set SECRET_KEY in .env for production."
        )
        return _FALLBACK_SECRET
    return secret_key


def _get_algorithm() -> str:
    return os.getenv("ALGORITHM", "HS256")


def _get_access_token_expire_minutes() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    claims: dict[str, Any] = {"sub": subject}
    if extra_claims:
        claims.update(extra_claims)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_get_access_token_expire_minutes())
    claims["exp"] = expires_at

    return jwt.encode(claims, _get_secret_key(), algorithm=_get_algorithm())


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret_key(), algorithms=[_get_algorithm()])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
