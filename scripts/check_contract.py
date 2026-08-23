#!/usr/bin/env python3
"""Fail CI when the public demo contract drifts from its 22 operations."""

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
    actual = {
        (method.upper(), path)
        for path, path_item in document["paths"].items()
        if path == "/health" or path.startswith("/api/v1/")
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if actual != EXPECTED_OPERATIONS:
        missing = sorted(EXPECTED_OPERATIONS - actual)
        unexpected = sorted(actual - EXPECTED_OPERATIONS)
        raise SystemExit(
            "API contract drifted from 22 operations. "
            f"Missing: {missing or 'none'}; unexpected: {unexpected or 'none'}"
        )
    print("PASS: OpenAPI exposes the exact 22-operation hackathon contract")


if __name__ == "__main__":
    main()
