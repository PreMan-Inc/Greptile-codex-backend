from datetime import UTC, datetime

from app.config import Settings
from app.domain import (
    ProjectRecord,
    ProjectStatus,
    Role,
    TaskPriority,
    TaskRecord,
    TaskStatus,
    UserRecord,
)
from app.errors import DuplicateEntityError
from app.repositories.base import Repository
from app.security import hash_password

DEMO_USER_ID = "00000000-0000-4000-8000-000000000001"
DEMO_PROJECT_ID = "10000000-0000-4000-8000-000000000001"
DEMO_TASK_ONE_ID = "20000000-0000-4000-8000-000000000001"
DEMO_TASK_TWO_ID = "20000000-0000-4000-8000-000000000002"
DEMO_TASK_IDS = frozenset({DEMO_TASK_ONE_ID, DEMO_TASK_TWO_ID})
SEED_TIMESTAMP = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def seed_demo_data(repository: Repository, settings: Settings) -> None:
    """Create a predictable demo workspace without overwriting user changes."""

    demo_user = repository.get_user_by_email(settings.demo_user_email)
    if demo_user is None:
        demo_user = UserRecord(
            id=DEMO_USER_ID,
            email=settings.demo_user_email.lower(),
            name="PreMan Demo",
            role=Role.ADMIN,
            password_hash=hash_password(settings.demo_user_password),
            created_at=SEED_TIMESTAMP,
            updated_at=SEED_TIMESTAMP,
        )
        try:
            repository.create_user(demo_user)
        except DuplicateEntityError:
            demo_user = repository.get_user_by_email(settings.demo_user_email)
            if demo_user is None:
                raise

    if repository.get_project(demo_user.id, DEMO_PROJECT_ID) is None:
        try:
            repository.create_project(
                ProjectRecord(
                    id=DEMO_PROJECT_ID,
                    owner_id=demo_user.id,
                    name="Storefront API",
                    description="Demo project monitored and tested automatically by PreMan.",
                    status=ProjectStatus.ACTIVE,
                    created_at=SEED_TIMESTAMP,
                    updated_at=SEED_TIMESTAMP,
                )
            )
        except DuplicateEntityError:
            pass

    demo_tasks = (
        TaskRecord(
            id=DEMO_TASK_ONE_ID,
            owner_id=demo_user.id,
            project_id=DEMO_PROJECT_ID,
            title="Verify login contract",
            description="Keep the authentication response compatible on every push.",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_at=SEED_TIMESTAMP,
            updated_at=SEED_TIMESTAMP,
        ),
        TaskRecord(
            id=DEMO_TASK_TWO_ID,
            owner_id=demo_user.id,
            project_id=DEMO_PROJECT_ID,
            title="Test health endpoint",
            description="Continuously verify uptime and the expected response schema.",
            status=TaskStatus.DONE,
            priority=TaskPriority.MEDIUM,
            created_at=SEED_TIMESTAMP,
            updated_at=SEED_TIMESTAMP,
        ),
    )
    for task in demo_tasks:
        if repository.get_task(demo_user.id, task.id) is None:
            try:
                repository.create_task(task)
            except DuplicateEntityError:
                pass
