#!/usr/bin/env python3
"""Fail CI when the preserved legacy contract drifts from its 22 operations."""

from app.main import app

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


def main() -> None:
    document = app.openapi()
    expected_server = "https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws"
    actual_servers = document.get("servers") or []
    if not actual_servers or actual_servers[0].get("url") != expected_server:
        raise SystemExit(f"OpenAPI must advertise the agent-test backend at {expected_server}")
    actual = {
        (method.upper(), path)
        for path, path_item in document["paths"].items()
        if path == "/health"
        or (path.startswith("/api/v1/") and not path.startswith("/api/v1/mock/"))
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if actual != EXPECTED_OPERATIONS:
        missing = sorted(EXPECTED_OPERATIONS - actual)
        unexpected = sorted(actual - EXPECTED_OPERATIONS)
        raise SystemExit(
            "Legacy API contract drifted from 22 operations. "
            f"Missing: {missing or 'none'}; unexpected: {unexpected or 'none'}"
        )
    print("PASS: OpenAPI exposes the exact preserved 22-operation legacy contract")


if __name__ == "__main__":
    main()
