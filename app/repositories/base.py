from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import (
    ProjectRecord,
    ProjectStatus,
    ResetTokenRecord,
    TaskRecord,
    TaskStatus,
    TokenRecord,
    UserRecord,
)


class Repository(ABC):
    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def create_user(self, user: UserRecord) -> UserRecord: ...

    @abstractmethod
    def get_user(self, user_id: str) -> UserRecord | None: ...

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserRecord | None: ...

    @abstractmethod
    def update_user(self, user: UserRecord) -> UserRecord: ...

    @abstractmethod
    def save_refresh_token(self, token: TokenRecord) -> None: ...

    @abstractmethod
    def get_refresh_token(self, token_hash: str) -> TokenRecord | None: ...

    @abstractmethod
    def revoke_refresh_token(self, token_hash: str) -> None: ...

    @abstractmethod
    def save_reset_token(self, token: ResetTokenRecord) -> None: ...

    @abstractmethod
    def consume_reset_token(self, token_hash: str) -> ResetTokenRecord | None: ...

    @abstractmethod
    def create_project(self, project: ProjectRecord) -> ProjectRecord: ...

    @abstractmethod
    def get_project(self, owner_id: str, project_id: str) -> ProjectRecord | None: ...

    @abstractmethod
    def list_projects(
        self, owner_id: str, status: ProjectStatus | None = None
    ) -> list[ProjectRecord]: ...

    @abstractmethod
    def update_project(self, project: ProjectRecord) -> ProjectRecord: ...

    @abstractmethod
    def delete_project(self, owner_id: str, project_id: str) -> bool: ...

    @abstractmethod
    def create_task(self, task: TaskRecord) -> TaskRecord: ...

    @abstractmethod
    def get_task(self, owner_id: str, task_id: str) -> TaskRecord | None: ...

    @abstractmethod
    def list_tasks(
        self,
        owner_id: str,
        project_id: str,
        status: TaskStatus | None = None,
    ) -> list[TaskRecord]: ...

    @abstractmethod
    def update_task(self, task: TaskRecord) -> TaskRecord: ...

    @abstractmethod
    def delete_task(self, owner_id: str, task_id: str) -> bool: ...
