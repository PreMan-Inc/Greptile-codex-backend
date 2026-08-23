from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EntityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserRecord(EntityModel):
    id: str
    email: EmailStr
    name: str
    role: Role = Role.USER
    password_hash: str
    auth_version: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectRecord(EntityModel):
    id: str
    owner_id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class TaskRecord(EntityModel):
    id: str
    owner_id: str
    project_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TokenRecord(EntityModel):
    token_hash: str
    user_id: str
    auth_version: int
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class ResetTokenRecord(EntityModel):
    token_hash: str
    user_id: str
    auth_version: int
    expires_at: datetime
    consumed: bool = False
    created_at: datetime = Field(default_factory=utc_now)


def json_payload(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
