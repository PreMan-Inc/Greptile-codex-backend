from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response, status

from app.config import Settings
from app.demo_protection import require_mutable_demo_resource
from app.dependencies import get_current_user, get_repository, get_runtime_settings
from app.domain import TaskRecord, TaskStatus, UserRecord
from app.errors import AppError
from app.repositories.base import Repository
from app.schemas import (
    TaskCreateRequest,
    TaskListResponse,
    TaskReplaceRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from app.seed import DEMO_TASK_IDS

router = APIRouter(tags=["Tasks"])


def _response(task: TaskRecord) -> TaskResponse:
    return TaskResponse.model_validate(task.model_dump())


def _get_owned_task(repository: Repository, owner_id: str, task_id: str) -> TaskRecord:
    task = repository.get_task(owner_id, task_id)
    if task is None:
        raise AppError(404, "task_not_found", "Task not found")
    return task


def _require_project(repository: Repository, owner_id: str, project_id: str) -> None:
    if repository.get_project(owner_id, project_id) is None:
        raise AppError(404, "project_not_found", "Project not found")


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
def list_tasks(
    project_id: str,
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> TaskListResponse:
    _require_project(repository, user.id, project_id)
    tasks = repository.list_tasks(user.id, project_id, task_status)
    return TaskListResponse(
        items=[_response(task) for task in tasks[offset : offset + limit]],
        total=len(tasks),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: str,
    payload: TaskCreateRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> TaskResponse:
    _require_project(repository, user.id, project_id)
    now = datetime.now(UTC)
    task = repository.create_task(
        TaskRecord(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            project_id=project_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            due_at=payload.due_at,
            created_at=now,
            updated_at=now,
        )
    )
    return _response(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> TaskResponse:
    return _response(_get_owned_task(repository, user.id, task_id))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdateRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> TaskResponse:
    require_mutable_demo_resource(settings, task_id, DEMO_TASK_IDS)
    task = _get_owned_task(repository, user.id, task_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        changes["updated_at"] = datetime.now(UTC)
        task = repository.update_task(task.model_copy(update=changes))
    return _response(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def replace_task(
    task_id: str,
    payload: TaskReplaceRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> TaskResponse:
    require_mutable_demo_resource(settings, task_id, DEMO_TASK_IDS)
    task = _get_owned_task(repository, user.id, task_id)
    replaced = repository.update_task(
        task.model_copy(
            update={
                **payload.model_dump(),
                "updated_at": datetime.now(UTC),
            }
        )
    )
    return _response(replaced)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_task(
    task_id: str,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> Response:
    require_mutable_demo_resource(settings, task_id, DEMO_TASK_IDS)
    if not repository.delete_task(user.id, task_id):
        raise AppError(404, "task_not_found", "Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
