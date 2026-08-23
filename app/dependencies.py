from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.domain import UserRecord
from app.errors import AppError
from app.repositories.base import Repository
from app.security import decode_token

bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_repository(request: Request) -> Repository:
    return request.app.state.repository


def get_runtime_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "authentication_required", "A Bearer access token is required")
    payload = decode_token(settings, credentials.credentials, "access")
    user = repository.get_user(str(payload["sub"]))
    if user is None or user.auth_version != int(payload["ver"]):
        raise AppError(401, "invalid_token", "The token is no longer valid")
    return user
