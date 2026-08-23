from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status

from app.config import Settings
from app.demo_protection import is_protected_demo_resource, require_mutable_demo_resource
from app.dependencies import get_current_user, get_repository, get_runtime_settings
from app.domain import ResetTokenRecord, Role, TokenRecord, UserRecord
from app.errors import AppError, DuplicateEntityError
from app.repositories.base import Repository
from app.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateMeRequest,
    UserPublic,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    token_digest,
    verify_password,
)
from app.seed import DEMO_USER_ID

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _public_user(user: UserRecord) -> UserPublic:
    return UserPublic.model_validate(user.model_dump(exclude={"password_hash", "auth_version"}))


def _ensure_strong_password(password: str) -> None:
    requirements = (
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
    )
    if not all(requirements):
        raise AppError(
            422,
            "weak_password",
            "Password must include an uppercase letter, a lowercase letter, and a number",
        )


def _issue_auth_response(
    user: UserRecord, repository: Repository, settings: Settings
) -> AuthResponse:
    access_token, _ = create_access_token(settings, user.id, user.auth_version)
    refresh_token, refresh_expires_at = create_refresh_token(settings, user.id, user.auth_version)
    repository.save_refresh_token(
        TokenRecord(
            token_hash=token_digest(refresh_token),
            user_id=user.id,
            auth_version=user.auth_version,
            expires_at=refresh_expires_at,
        )
    )
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_minutes * 60,
        user=_public_user(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> AuthResponse:
    _ensure_strong_password(payload.password)
    now = datetime.now(UTC)
    user = UserRecord(
        id=str(uuid.uuid4()),
        email=payload.email.lower(),
        name=payload.name,
        role=Role.USER,
        password_hash=hash_password(payload.password),
        created_at=now,
        updated_at=now,
    )
    try:
        repository.create_user(user)
    except DuplicateEntityError as exc:
        raise AppError(409, "email_in_use", "An account already exists for this email") from exc
    return _issue_auth_response(user, repository, settings)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> AuthResponse:
    user = repository.get_user_by_email(payload.email.lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(401, "invalid_credentials", "Email or password is incorrect")
    return _issue_auth_response(user, repository, settings)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    payload: RefreshRequest,
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> AuthResponse:
    claims = decode_token(settings, payload.refresh_token, "refresh")
    digest = token_digest(payload.refresh_token)
    session = repository.get_refresh_token(digest)
    user = repository.get_user(str(claims["sub"]))
    if (
        session is None
        or user is None
        or session.user_id != user.id
        or session.auth_version != user.auth_version
        or int(claims["ver"]) != user.auth_version
    ):
        raise AppError(401, "invalid_refresh_token", "The refresh token is invalid or revoked")
    repository.revoke_refresh_token(digest)
    return _issue_auth_response(user, repository, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(
    payload: LogoutRequest,
    repository: Repository = Depends(get_repository),
) -> Response:
    repository.revoke_refresh_token(token_digest(payload.refresh_token))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
def get_me(user: UserRecord = Depends(get_current_user)) -> UserPublic:
    return _public_user(user)


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UpdateMeRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> UserPublic:
    require_mutable_demo_resource(settings, user.id, {DEMO_USER_ID})
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return _public_user(user)
    changes["updated_at"] = datetime.now(UTC)
    updated = repository.update_user(user.model_copy(update=changes))
    return _public_user(updated)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> ForgotPasswordResponse:
    user = repository.get_user_by_email(payload.email.lower())
    reset_token: str | None = None
    if user is not None and not is_protected_demo_resource(settings, user.id, {DEMO_USER_ID}):
        reset_token, expires_at = create_reset_token(settings, user.id, user.auth_version)
        repository.save_reset_token(
            ResetTokenRecord(
                token_hash=token_digest(reset_token),
                user_id=user.id,
                auth_version=user.auth_version,
                expires_at=expires_at,
            )
        )
    return ForgotPasswordResponse(
        message="If that account exists, password reset instructions have been issued.",
        reset_token=reset_token if settings.expose_demo_tokens else None,
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> MessageResponse:
    _ensure_strong_password(payload.new_password)
    claims = decode_token(settings, payload.reset_token, "password_reset")
    require_mutable_demo_resource(settings, str(claims["sub"]), {DEMO_USER_ID})
    token = repository.consume_reset_token(token_digest(payload.reset_token))
    user = repository.get_user(str(claims["sub"]))
    if (
        token is None
        or user is None
        or token.user_id != user.id
        or token.auth_version != user.auth_version
        or int(claims["ver"]) != user.auth_version
    ):
        raise AppError(400, "invalid_reset_token", "The reset token is invalid or already used")
    repository.update_user(
        user.model_copy(
            update={
                "password_hash": hash_password(payload.new_password),
                "auth_version": user.auth_version + 1,
                "updated_at": datetime.now(UTC),
            }
        )
    )
    return MessageResponse(message="Password reset successfully")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> MessageResponse:
    require_mutable_demo_resource(settings, user.id, {DEMO_USER_ID})
    if not verify_password(payload.current_password, user.password_hash):
        raise AppError(401, "invalid_current_password", "Current password is incorrect")
    _ensure_strong_password(payload.new_password)
    repository.update_user(
        user.model_copy(
            update={
                "password_hash": hash_password(payload.new_password),
                "auth_version": user.auth_version + 1,
                "updated_at": datetime.now(UTC),
            }
        )
    )
    return MessageResponse(message="Password changed successfully")
