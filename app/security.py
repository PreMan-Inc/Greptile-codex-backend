from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.config import Settings
from app.errors import AppError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _encode_token(
    settings: Settings,
    user_id: str,
    auth_version: int,
    token_type: Literal["access", "refresh", "password_reset"],
    expires_delta: timedelta,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    payload = {
        "sub": user_id,
        "iss": settings.jwt_issuer,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        "ver": auth_version,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_at


def create_access_token(
    settings: Settings, user_id: str, auth_version: int
) -> tuple[str, datetime]:
    return _encode_token(
        settings,
        user_id,
        auth_version,
        "access",
        timedelta(minutes=settings.access_token_minutes),
    )


def create_refresh_token(
    settings: Settings, user_id: str, auth_version: int
) -> tuple[str, datetime]:
    return _encode_token(
        settings,
        user_id,
        auth_version,
        "refresh",
        timedelta(days=settings.refresh_token_days),
    )


def create_reset_token(settings: Settings, user_id: str, auth_version: int) -> tuple[str, datetime]:
    return _encode_token(
        settings,
        user_id,
        auth_version,
        "password_reset",
        timedelta(minutes=settings.reset_token_minutes),
    )


def decode_token(
    settings: Settings,
    token: str,
    expected_type: Literal["access", "refresh", "password_reset"],
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "iss", "iat", "nbf", "exp", "jti", "type", "ver"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(401, "token_expired", "The token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(401, "invalid_token", "The token is invalid") from exc

    if payload.get("type") != expected_type:
        raise AppError(401, "invalid_token_type", f"Expected a {expected_type} token")
    return payload
