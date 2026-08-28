from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain import ProjectStatus, Role, TaskPriority, TaskStatus


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UserPublic(APIModel):
    id: str
    email: EmailStr
    name: str
    role: Role
    created_at: datetime
    updated_at: datetime


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=80)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(APIModel):
    refresh_token: str = Field(min_length=20)


class UpdateMeRequest(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)


class ForgotPasswordRequest(APIModel):
    email: EmailStr


class ResetPasswordRequest(APIModel):
    reset_token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(APIModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AuthResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class MessageResponse(APIModel):
    message: str


class ForgotPasswordResponse(MessageResponse):
    reset_token: str | None = None


class ProjectCreateRequest(APIModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdateRequest(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None


class ProjectReplaceRequest(APIModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(max_length=2000)
    status: ProjectStatus


class ProjectResponse(APIModel):
    id: str
    owner_id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(APIModel):
    items: list[ProjectResponse]
    total: int
    limit: int
    offset: int


class TaskCreateRequest(APIModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: datetime | None = None

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class TaskUpdateRequest(APIModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class TaskReplaceRequest(APIModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(max_length=4000)
    status: TaskStatus
    priority: TaskPriority
    due_at: datetime | None

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class TaskResponse(APIModel):
    id: str
    owner_id: str
    project_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(APIModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class HealthResponse(APIModel):
    status: str = Field(description="`ok` when the service is serving traffic.")
    service: str = Field(description="The service's own name, for multi-service dashboards.")
    environment: str = Field(description="Which deployment answered: development, demo or production.")
    storage: str = Field(description="The storage backend currently in use.")
    version: str = Field(description="The running application version.")
    timestamp: datetime = Field(description="When this answer was produced, in UTC.")


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    field: str | None = None
    message: str | None = None


class ErrorBody(APIModel):
    code: str
    message: str
    details: list[dict[str, Any]] | dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(APIModel):
    error: ErrorBody
