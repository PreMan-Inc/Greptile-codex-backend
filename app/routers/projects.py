from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response, status

from app.config import Settings
from app.demo_protection import require_mutable_demo_resource
from app.dependencies import get_current_user, get_repository, get_runtime_settings
from app.domain import ProjectRecord, ProjectStatus, UserRecord
from app.errors import AppError
from app.repositories.base import Repository
from app.schemas import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.seed import DEMO_PROJECT_ID

router = APIRouter(prefix="/projects", tags=["Projects"])


def _response(project: ProjectRecord) -> ProjectResponse:
    return ProjectResponse.model_validate(project.model_dump())


def _get_owned_project(repository: Repository, owner_id: str, project_id: str) -> ProjectRecord:
    project = repository.get_project(owner_id, project_id)
    if project is None:
        raise AppError(404, "project_not_found", "Project not found")
    return project


@router.get("", response_model=ProjectListResponse)
def list_projects(
    project_status: ProjectStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> ProjectListResponse:
    projects = repository.list_projects(user.id, project_status)
    return ProjectListResponse(
        items=[_response(project) for project in projects[offset : offset + limit]],
        total=len(projects),
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> ProjectResponse:
    now = datetime.now(UTC)
    project = repository.create_project(
        ProjectRecord(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
    )
    return _response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
) -> ProjectResponse:
    return _response(_get_owned_project(repository, user.id, project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> ProjectResponse:
    require_mutable_demo_resource(settings, project_id, {DEMO_PROJECT_ID})
    project = _get_owned_project(repository, user.id, project_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        changes["updated_at"] = datetime.now(UTC)
        project = repository.update_project(project.model_copy(update=changes))
    return _response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_project(
    project_id: str,
    user: UserRecord = Depends(get_current_user),
    repository: Repository = Depends(get_repository),
    settings: Settings = Depends(get_runtime_settings),
) -> Response:
    require_mutable_demo_resource(settings, project_id, {DEMO_PROJECT_ID})
    if not repository.delete_project(user.id, project_id):
        raise AppError(404, "project_not_found", "Project not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
