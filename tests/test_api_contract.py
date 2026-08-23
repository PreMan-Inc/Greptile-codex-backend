from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.domain import ResetTokenRecord
from app.main import app
from app.security import create_reset_token, token_digest
from app.seed import DEMO_PROJECT_ID, DEMO_TASK_ONE_ID, DEMO_USER_ID

DEMO_EMAIL = "demo@preman.live"
DEMO_PASSWORD = "PremanDemo123!"

EXPECTED_OPERATIONS = {
    ("GET", "/health"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/me"),
    ("PATCH", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    ("POST", "/api/v1/auth/change-password"),
    ("GET", "/api/v1/projects"),
    ("POST", "/api/v1/projects"),
    ("GET", "/api/v1/projects/{project_id}"),
    ("PUT", "/api/v1/projects/{project_id}"),
    ("PATCH", "/api/v1/projects/{project_id}"),
    ("DELETE", "/api/v1/projects/{project_id}"),
    ("GET", "/api/v1/projects/{project_id}/tasks"),
    ("POST", "/api/v1/projects/{project_id}/tasks"),
    ("GET", "/api/v1/tasks/{task_id}"),
    ("PUT", "/api/v1/tasks/{task_id}"),
    ("PATCH", "/api/v1/tasks/{task_id}"),
    ("DELETE", "/api/v1/tasks/{task_id}"),
}


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def unique_user(prefix: str = "contract") -> tuple[str, str]:
    suffix = uuid4().hex[:12]
    return f"{prefix}-{suffix}@example.com", f"Secure-{suffix}-Aa1!"


def register(client: TestClient, *, prefix: str = "contract") -> tuple[str, str, dict[str, object]]:
    email, password = unique_user(prefix)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Contract User"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    user = body["user"]
    assert user["email"] == email
    assert "password" not in user
    assert "password_hash" not in user
    return email, password, user


def login(client: TestClient, email: str, password: str) -> dict[str, object]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20
    assert isinstance(body["refresh_token"], str) and len(body["refresh_token"]) > 20
    assert body["expires_in"] > 0
    return body


def headers(access_token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {access_token}"}


def assert_error(response, *, status: int, code: str | None = None) -> dict[str, object]:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert isinstance(body["error"]["message"], str)
    if code is not None:
        assert body["error"]["code"] == code
    return body


def test_openapi_contains_exactly_the_22_operation_contract(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()

    operations = {
        (method.upper(), path)
        for path, path_item in document["paths"].items()
        if path == "/health" or path.startswith("/api/v1/")
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    assert operations == EXPECTED_OPERATIONS
    assert len(operations) == 22

    operation_ids = []
    for method, path in operations:
        operation = document["paths"][path][method.lower()]
        assert operation["summary"]
        assert operation["tags"]
        operation_ids.append(operation["operationId"])
    assert len(operation_ids) == len(set(operation_ids))


@pytest.mark.parametrize("path", ["/", "/ready", "/health", "/docs", "/openapi.json"])
def test_operational_routes_are_available(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200


def test_health_is_machine_readable(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["service"]
    assert body["environment"] in {"development", "test", "demo", "production"}
    assert body["storage"] in {"memory", "dynamodb"}
    assert body["version"]
    assert body["timestamp"].endswith(("Z", "+00:00"))


def test_seeded_demo_user_and_project_are_ready(client: TestClient) -> None:
    auth = login(client, DEMO_EMAIL, DEMO_PASSWORD)
    token = str(auth["access_token"])

    me = client.get("/api/v1/auth/me", headers=headers(token))
    assert me.status_code == 200
    assert me.json()["id"] == "00000000-0000-4000-8000-000000000001"
    assert me.json()["email"] == DEMO_EMAIL

    projects = client.get("/api/v1/projects", headers=headers(token))
    assert projects.status_code == 200
    body = projects.json()
    assert body["total"] >= 1
    assert body["limit"] >= len(body["items"])
    seeded = next(
        project
        for project in body["items"]
        if project["id"] == "10000000-0000-4000-8000-000000000001"
    )

    tasks = client.get(f"/api/v1/projects/{seeded['id']}/tasks", headers=headers(token))
    assert tasks.status_code == 200
    assert tasks.json()["total"] >= 2


def test_registration_profile_refresh_and_logout_lifecycle(client: TestClient) -> None:
    email, password, user = register(client, prefix="auth")

    duplicate = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Duplicate User"},
    )
    assert_error(duplicate, status=409)

    assert_error(
        client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"}),
        status=401,
    )

    auth = login(client, email, password)
    access_token = str(auth["access_token"])
    refresh_token = str(auth["refresh_token"])
    assert auth["user"]["id"] == user["id"]

    me = client.get("/api/v1/auth/me", headers=headers(access_token))
    assert me.status_code == 200
    assert me.json()["email"] == email

    updated = client.patch(
        "/api/v1/auth/me",
        headers=headers(access_token),
        json={"name": "Updated Contract User"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Contract User"

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    refreshed_body = refreshed.json()
    assert refreshed_body["refresh_token"] != refresh_token

    # Rotation makes the previous token unusable.
    assert_error(
        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token}),
        status=401,
    )

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed_body["refresh_token"]},
    )
    assert logout.status_code == 204
    assert not logout.content

    assert_error(
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refreshed_body["refresh_token"]},
        ),
        status=401,
    )


def test_password_recovery_and_change_lifecycle(client: TestClient) -> None:
    email, original_password, _ = register(client, prefix="password")
    reset_password = "Reset-Password-Aa2!"
    final_password = "Final-Password-Aa3!"

    # Unknown accounts receive the same generic success response and leak no token.
    unknown = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": f"missing-{uuid4().hex[:8]}@example.com"},
    )
    assert unknown.status_code == 200
    assert unknown.json().get("reset_token") is None

    forgot = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert isinstance(reset_token, str) and len(reset_token) > 20

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": reset_token, "new_password": reset_password},
    )
    assert reset.status_code == 200

    assert_error(
        client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": original_password},
        ),
        status=401,
    )
    assert_error(
        client.post(
            "/api/v1/auth/reset-password",
            json={"reset_token": reset_token, "new_password": reset_password},
        ),
        status=400,
    )

    auth = login(client, email, reset_password)
    changed = client.post(
        "/api/v1/auth/change-password",
        headers=headers(str(auth["access_token"])),
        json={
            "current_password": reset_password,
            "new_password": final_password,
        },
    )
    assert changed.status_code == 200

    assert_error(
        client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": reset_password},
        ),
        status=401,
    )
    login(client, email, final_password)


def test_project_and_task_crud_lifecycle(client: TestClient) -> None:
    email, password, _ = register(client, prefix="crud")
    token = str(login(client, email, password)["access_token"])
    auth_headers = headers(token)

    empty = client.get("/api/v1/projects", headers=auth_headers)
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}

    created = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "name": "Contract Project",
            "description": "Project lifecycle coverage",
            "status": "active",
        },
    )
    assert created.status_code == 201
    project = created.json()
    project_id = project["id"]
    assert project["name"] == "Contract Project"
    assert project["owner_id"]

    fetched = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json() == project

    replaced = client.put(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
        json={
            "name": "Replaced Contract Project",
            "description": "Complete replacement coverage",
            "status": "active",
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["name"] == "Replaced Contract Project"
    assert replaced.json()["description"] == "Complete replacement coverage"

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
        json={"name": "Updated Contract Project", "status": "archived"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Contract Project"
    assert updated.json()["status"] == "archived"

    tasks = client.get(f"/api/v1/projects/{project_id}/tasks", headers=auth_headers)
    assert tasks.status_code == 200
    assert tasks.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}

    created_task = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=auth_headers,
        json={
            "title": "Exercise all task routes",
            "description": "Created by pytest",
            "status": "todo",
            "priority": "high",
        },
    )
    assert created_task.status_code == 201, created_task.text
    task = created_task.json()
    task_id = task["id"]
    assert task["project_id"] == project_id
    assert task["status"] == "todo"

    task_list = client.get(
        f"/api/v1/projects/{project_id}/tasks?limit=1&offset=0",
        headers=auth_headers,
    )
    assert task_list.status_code == 200
    assert task_list.json()["total"] == 1
    assert task_list.json()["limit"] == 1

    fetched_task = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert fetched_task.status_code == 200
    assert fetched_task.json() == task

    replaced_task = client.put(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "Replaced task contract",
            "description": "All replace fields are explicit",
            "status": "in_progress",
            "priority": "low",
            "due_at": "2026-09-01T12:00:00Z",
        },
    )
    assert replaced_task.status_code == 200
    assert replaced_task.json()["title"] == "Replaced task contract"
    assert replaced_task.json()["status"] == "in_progress"

    updated_task = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers,
        json={"status": "done", "priority": "critical"},
    )
    assert updated_task.status_code == 200
    assert updated_task.json()["status"] == "done"
    assert updated_task.json()["priority"] == "critical"

    deleted_task = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert deleted_task.status_code == 204
    assert_error(client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers), status=404)

    deleted_project = client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert deleted_project.status_code == 204
    assert_error(
        client.get(f"/api/v1/projects/{project_id}", headers=auth_headers),
        status=404,
    )


def test_resources_are_owner_scoped(client: TestClient) -> None:
    first_email, first_password, _ = register(client, prefix="owner-a")
    second_email, second_password, _ = register(client, prefix="owner-b")
    first_headers = headers(str(login(client, first_email, first_password)["access_token"]))
    second_headers = headers(str(login(client, second_email, second_password)["access_token"]))

    project = client.post(
        "/api/v1/projects",
        headers=first_headers,
        json={"name": "Private Project", "description": "Owner only"},
    ).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        headers=first_headers,
        json={"title": "Private Task", "description": "Owner only"},
    ).json()

    assert_error(
        client.get(f"/api/v1/projects/{project['id']}", headers=second_headers),
        status=404,
    )
    assert_error(
        client.put(
            f"/api/v1/projects/{project['id']}",
            headers=second_headers,
            json={
                "name": "Stolen Project",
                "description": "Not the owner",
                "status": "active",
            },
        ),
        status=404,
    )
    assert_error(
        client.patch(
            f"/api/v1/projects/{project['id']}",
            headers=second_headers,
            json={"name": "Stolen Project"},
        ),
        status=404,
    )
    assert_error(
        client.get(f"/api/v1/tasks/{task['id']}", headers=second_headers),
        status=404,
    )
    assert_error(
        client.put(
            f"/api/v1/tasks/{task['id']}",
            headers=second_headers,
            json={
                "title": "Stolen Task",
                "description": "Not the owner",
                "status": "todo",
                "priority": "medium",
                "due_at": None,
            },
        ),
        status=404,
    )
    assert_error(
        client.delete(f"/api/v1/tasks/{task['id']}", headers=second_headers),
        status=404,
    )


def test_auth_and_validation_errors_use_one_envelope(client: TestClient) -> None:
    assert_error(client.get("/api/v1/projects"), status=401)

    invalid = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "name": "x"},
    )
    body = assert_error(invalid, status=422)
    assert body["error"]["details"]

    email, password, _ = register(client, prefix="validation")
    token = str(login(client, email, password)["access_token"])
    invalid_project = client.post(
        "/api/v1/projects",
        headers=headers(token),
        json={"name": "x", "unexpected": True},
    )
    assert_error(invalid_project, status=422)


def test_common_rest_methods_and_cors_preflight_are_available(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    methods = {
        method.upper()
        for path, path_item in document["paths"].items()
        if path == "/health" or path.startswith("/api/v1/")
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    assert methods == {"GET", "POST", "PUT", "PATCH", "DELETE"}

    preflight = client.options(
        "/api/v1/projects/example",
        headers={
            "origin": "https://example.com",
            "access-control-request-method": "PUT",
            "access-control-request-headers": "authorization,content-type",
        },
    )
    assert preflight.status_code == 200
    allowed = preflight.headers["access-control-allow-methods"]
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        assert method in allowed

    unsupported = client.request("TRACE", "/api/v1/projects")
    assert_error(unsupported, status=405, code="http_error")


def test_agent_edge_matrix_for_replacement_filters_and_boundaries(client: TestClient) -> None:
    email, password, _ = register(client, prefix="agent-edges")
    auth_headers = headers(str(login(client, email, password)["access_token"]))

    active = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Active Edge Project", "description": "Initial"},
    ).json()
    archived = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Archived Edge Project", "status": "archived"},
    ).json()

    missing_replace_fields = client.put(
        f"/api/v1/projects/{active['id']}",
        headers=auth_headers,
        json={"name": "Incomplete replacement"},
    )
    assert_error(missing_replace_fields, status=422, code="validation_error")

    replaced = client.put(
        f"/api/v1/projects/{active['id']}",
        headers=auth_headers,
        json={
            "name": "Fully Replaced Project",
            "description": "PUT replaces the complete writable representation",
            "status": "active",
        },
    )
    assert replaced.status_code == 200
    patched = client.patch(
        f"/api/v1/projects/{active['id']}",
        headers=auth_headers,
        json={"name": "Partially Patched Project"},
    )
    assert patched.status_code == 200
    assert patched.json()["description"] == "PUT replaces the complete writable representation"

    filtered = client.get(
        "/api/v1/projects?status=archived&limit=1&offset=0",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == archived["id"]
    for query in ("limit=0", "limit=101", "offset=-1", "status=unknown"):
        assert_error(
            client.get(f"/api/v1/projects?{query}", headers=auth_headers),
            status=422,
            code="validation_error",
        )

    naive_due_at = client.post(
        f"/api/v1/projects/{active['id']}/tasks",
        headers=auth_headers,
        json={"title": "Naive date", "due_at": "2026-09-01T12:00:00"},
    )
    assert_error(naive_due_at, status=422, code="validation_error")

    task = client.post(
        f"/api/v1/projects/{active['id']}/tasks",
        headers=auth_headers,
        json={"title": "Edge Task", "status": "todo", "priority": "high"},
    ).json()
    incomplete_task = client.put(
        f"/api/v1/tasks/{task['id']}",
        headers=auth_headers,
        json={"title": "Incomplete"},
    )
    assert_error(incomplete_task, status=422, code="validation_error")

    replaced_task = client.put(
        f"/api/v1/tasks/{task['id']}",
        headers=auth_headers,
        json={
            "title": "Fully Replaced Task",
            "description": "Complete representation",
            "status": "in_progress",
            "priority": "critical",
            "due_at": "2026-09-01T12:00:00Z",
        },
    )
    assert replaced_task.status_code == 200
    assert replaced_task.json()["priority"] == "critical"

    cleared_due_at = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=auth_headers,
        json={"due_at": None, "status": "done"},
    )
    assert cleared_due_at.status_code == 200
    assert cleared_due_at.json()["due_at"] is None

    invalid_patch_date = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=auth_headers,
        json={"due_at": "2026-09-01T12:00:00"},
    )
    assert_error(invalid_patch_date, status=422, code="validation_error")

    assert client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers).status_code == 204
    assert_error(
        client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers),
        status=404,
        code="task_not_found",
    )


def test_seeded_demo_identity_and_resources_are_read_only_in_demo_mode(
    client: TestClient,
) -> None:
    settings = client.app.state.settings
    repository = client.app.state.repository
    previous_environment = settings.app_env
    settings.app_env = "demo"

    try:
        auth = login(client, DEMO_EMAIL, DEMO_PASSWORD)
        access_token = str(auth["access_token"])
        auth_headers = headers(access_token)

        forgot = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": DEMO_EMAIL},
        )
        assert forgot.status_code == 200
        assert forgot.json().get("reset_token") is None

        assert_error(
            client.put(
                f"/api/v1/projects/{DEMO_PROJECT_ID}",
                headers=auth_headers,
                json={
                    "name": "Mutated Seed",
                    "description": "Protected",
                    "status": "active",
                },
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.patch(
                "/api/v1/auth/me",
                headers=auth_headers,
                json={"name": "Mutated Demo"},
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.post(
                "/api/v1/auth/change-password",
                headers=auth_headers,
                json={
                    "current_password": DEMO_PASSWORD,
                    "new_password": "Changed-Demo-Aa1!",
                },
            ),
            status=403,
            code="demo_resource_immutable",
        )

        demo_user = repository.get_user(DEMO_USER_ID)
        assert demo_user is not None
        reset_token, expires_at = create_reset_token(settings, demo_user.id, demo_user.auth_version)
        repository.save_reset_token(
            ResetTokenRecord(
                token_hash=token_digest(reset_token),
                user_id=demo_user.id,
                auth_version=demo_user.auth_version,
                expires_at=expires_at,
            )
        )
        assert_error(
            client.post(
                "/api/v1/auth/reset-password",
                json={
                    "reset_token": reset_token,
                    "new_password": "Changed-Demo-Aa1!",
                },
            ),
            status=403,
            code="demo_resource_immutable",
        )

        assert_error(
            client.put(
                f"/api/v1/tasks/{DEMO_TASK_ONE_ID}",
                headers=auth_headers,
                json={
                    "title": "Mutated Seed",
                    "description": "Protected",
                    "status": "done",
                    "priority": "high",
                    "due_at": None,
                },
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.patch(
                f"/api/v1/projects/{DEMO_PROJECT_ID}",
                headers=auth_headers,
                json={"name": "Mutated Seed"},
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.delete(
                f"/api/v1/projects/{DEMO_PROJECT_ID}",
                headers=auth_headers,
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.patch(
                f"/api/v1/tasks/{DEMO_TASK_ONE_ID}",
                headers=auth_headers,
                json={"status": "done"},
            ),
            status=403,
            code="demo_resource_immutable",
        )
        assert_error(
            client.delete(
                f"/api/v1/tasks/{DEMO_TASK_ONE_ID}",
                headers=auth_headers,
            ),
            status=403,
            code="demo_resource_immutable",
        )

        created_project = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "Disposable Demo Project"},
        )
        assert created_project.status_code == 201
        project_id = created_project.json()["id"]
        assert (
            client.patch(
                f"/api/v1/projects/{project_id}",
                headers=auth_headers,
                json={"description": "Still mutable"},
            ).status_code
            == 200
        )

        created_task = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=auth_headers,
            json={"title": "Disposable Demo Task"},
        )
        assert created_task.status_code == 201
        task_id = created_task.json()["id"]
        assert (
            client.patch(
                f"/api/v1/tasks/{task_id}",
                headers=auth_headers,
                json={"status": "done"},
            ).status_code
            == 200
        )
        assert client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers).status_code == 204
        assert (
            client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers).status_code == 204
        )

        # Every denied mutation left the published demo credentials intact.
        login(client, DEMO_EMAIL, DEMO_PASSWORD)
    finally:
        settings.app_env = previous_environment
