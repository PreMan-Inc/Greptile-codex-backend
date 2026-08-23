from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock

from app.domain import (
    ProjectRecord,
    ProjectStatus,
    ResetTokenRecord,
    TaskRecord,
    TaskStatus,
    TokenRecord,
    UserRecord,
)
from app.errors import DuplicateEntityError
from app.repositories.base import Repository


class MemoryRepository(Repository):
    """Thread-safe local repository used by development and the test suite."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._users: dict[str, UserRecord] = {}
        self._users_by_email: dict[str, str] = {}
        self._refresh_tokens: dict[str, TokenRecord] = {}
        self._reset_tokens: dict[str, ResetTokenRecord] = {}
        self._projects: dict[str, ProjectRecord] = {}
        self._tasks: dict[str, TaskRecord] = {}

    def initialize(self) -> None:
        return None

    def create_user(self, user: UserRecord) -> UserRecord:
        normalized = user.email.lower()
        with self._lock:
            if normalized in self._users_by_email or user.id in self._users:
                raise DuplicateEntityError("user already exists")
            self._users[user.id] = user.model_copy(deep=True)
            self._users_by_email[normalized] = user.id
        return user.model_copy(deep=True)

    def get_user(self, user_id: str) -> UserRecord | None:
        with self._lock:
            user = self._users.get(user_id)
            return user.model_copy(deep=True) if user else None

    def get_user_by_email(self, email: str) -> UserRecord | None:
        with self._lock:
            user_id = self._users_by_email.get(email.lower())
            user = self._users.get(user_id) if user_id else None
            return user.model_copy(deep=True) if user else None

    def update_user(self, user: UserRecord) -> UserRecord:
        with self._lock:
            previous = self._users.get(user.id)
            if previous and previous.email.lower() != user.email.lower():
                self._users_by_email.pop(previous.email.lower(), None)
            self._users[user.id] = user.model_copy(deep=True)
            self._users_by_email[user.email.lower()] = user.id
        return user.model_copy(deep=True)

    def save_refresh_token(self, token: TokenRecord) -> None:
        with self._lock:
            self._refresh_tokens[token.token_hash] = token.model_copy(deep=True)

    def get_refresh_token(self, token_hash: str) -> TokenRecord | None:
        with self._lock:
            token = self._refresh_tokens.get(token_hash)
            if not token or token.revoked or token.expires_at <= datetime.now(UTC):
                return None
            return token.model_copy(deep=True)

    def revoke_refresh_token(self, token_hash: str) -> None:
        with self._lock:
            token = self._refresh_tokens.get(token_hash)
            if token:
                self._refresh_tokens[token_hash] = token.model_copy(update={"revoked": True})

    def save_reset_token(self, token: ResetTokenRecord) -> None:
        with self._lock:
            self._reset_tokens[token.token_hash] = token.model_copy(deep=True)

    def consume_reset_token(self, token_hash: str) -> ResetTokenRecord | None:
        with self._lock:
            token = self._reset_tokens.get(token_hash)
            if not token or token.consumed or token.expires_at <= datetime.now(UTC):
                return None
            self._reset_tokens[token_hash] = token.model_copy(update={"consumed": True})
            return token.model_copy(deep=True)

    def create_project(self, project: ProjectRecord) -> ProjectRecord:
        with self._lock:
            if project.id in self._projects:
                raise DuplicateEntityError("project already exists")
            self._projects[project.id] = project.model_copy(deep=True)
        return project.model_copy(deep=True)

    def get_project(self, owner_id: str, project_id: str) -> ProjectRecord | None:
        with self._lock:
            project = self._projects.get(project_id)
            if not project or project.owner_id != owner_id:
                return None
            return project.model_copy(deep=True)

    def list_projects(
        self, owner_id: str, status: ProjectStatus | None = None
    ) -> list[ProjectRecord]:
        with self._lock:
            projects = [
                project.model_copy(deep=True)
                for project in self._projects.values()
                if project.owner_id == owner_id and (status is None or project.status == status)
            ]
        return sorted(projects, key=lambda item: (item.created_at, item.id), reverse=True)

    def update_project(self, project: ProjectRecord) -> ProjectRecord:
        with self._lock:
            self._projects[project.id] = project.model_copy(deep=True)
        return project.model_copy(deep=True)

    def delete_project(self, owner_id: str, project_id: str) -> bool:
        with self._lock:
            project = self._projects.get(project_id)
            if not project or project.owner_id != owner_id:
                return False
            del self._projects[project_id]
            self._tasks = {
                task_id: task
                for task_id, task in self._tasks.items()
                if task.project_id != project_id
            }
            return True

    def create_task(self, task: TaskRecord) -> TaskRecord:
        with self._lock:
            if task.id in self._tasks:
                raise DuplicateEntityError("task already exists")
            self._tasks[task.id] = task.model_copy(deep=True)
        return task.model_copy(deep=True)

    def get_task(self, owner_id: str, task_id: str) -> TaskRecord | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.owner_id != owner_id:
                return None
            return task.model_copy(deep=True)

    def list_tasks(
        self,
        owner_id: str,
        project_id: str,
        status: TaskStatus | None = None,
    ) -> list[TaskRecord]:
        with self._lock:
            tasks = [
                task.model_copy(deep=True)
                for task in self._tasks.values()
                if task.owner_id == owner_id
                and task.project_id == project_id
                and (status is None or task.status == status)
            ]
        return sorted(tasks, key=lambda item: (item.created_at, item.id), reverse=True)

    def update_task(self, task: TaskRecord) -> TaskRecord:
        with self._lock:
            self._tasks[task.id] = task.model_copy(deep=True)
        return task.model_copy(deep=True)

    def delete_task(self, owner_id: str, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.owner_id != owner_id:
                return False
            del self._tasks[task_id]
            return True
