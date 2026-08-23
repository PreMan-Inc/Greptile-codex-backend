#!/usr/bin/env python3
"""Exercise the exact 20-operation API contract through real HTTP.

The runner creates a unique temporary user and owns every mutable resource it
touches. The seeded demo account is only used to prove deterministic login.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
DEMO_EMAIL = os.getenv("DEMO_USER_EMAIL", os.getenv("DEMO_EMAIL", "demo@preman.live"))
DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", os.getenv("DEMO_PASSWORD", "PremanDemo123!"))


@dataclass
class Response:
    status: int
    body: Any


class SmokeFailure(RuntimeError):
    pass


def request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    token: str | None = None,
    expected: int | tuple[int, ...] = 200,
) -> Response:
    headers = {"accept": "application/json"}
    data = None
    if json_body is not None:
        headers["content-type"] = "application/json"
        data = json.dumps(json_body).encode()
    if token:
        headers["authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as raw:
            status = raw.status
            payload = raw.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = exc.read()
    except (OSError, TimeoutError) as exc:
        raise SmokeFailure(f"{method} {path} could not connect: {exc}") from exc

    try:
        body: Any = json.loads(payload) if payload else None
    except json.JSONDecodeError:
        body = payload.decode(errors="replace")

    accepted = (expected,) if isinstance(expected, int) else expected
    if status not in accepted:
        raise SmokeFailure(f"{method} {path}: expected {accepted}, received {status}: {body!r}")
    return Response(status=status, body=body)


def value(payload: Any, key: str) -> Any:
    """Read a key from either a flat body or a conventional data wrapper."""
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        if isinstance(payload.get("data"), dict) and key in payload["data"]:
            return payload["data"][key]
    raise SmokeFailure(f"Response does not contain {key!r}: {payload!r}")


def step(number: int, method: str, path: str) -> None:
    print(f"[operation {number:02d}] {method:<6} {path}")


def main() -> int:
    suffix = uuid4().hex[:12]
    email = f"preman-smoke-{suffix}@example.com"
    password = f"Smoke-{suffix}-Aa1!"
    reset_password = f"Reset-{suffix}-Aa2!"
    final_password = f"Final-{suffix}-Aa3!"

    step(1, "GET", "/health")
    request("GET", "/health")

    step(2, "POST", "/api/v1/auth/register")
    request(
        "POST",
        "/api/v1/auth/register",
        json_body={"email": email, "password": password, "name": "Smoke User"},
        expected=(200, 201),
    )

    step(3, "POST", "/api/v1/auth/login")
    login = request(
        "POST",
        "/api/v1/auth/login",
        json_body={"email": email, "password": password},
    ).body
    access_token = value(login, "access_token")
    refresh_token = value(login, "refresh_token")

    step(4, "POST", "/api/v1/auth/refresh")
    refreshed = request(
        "POST", "/api/v1/auth/refresh", json_body={"refresh_token": refresh_token}
    ).body
    access_token = value(refreshed, "access_token")
    rotated_refresh = value(refreshed, "refresh_token")

    step(5, "POST", "/api/v1/auth/logout")
    request(
        "POST",
        "/api/v1/auth/logout",
        json_body={"refresh_token": rotated_refresh},
        expected=(200, 204),
    )
    # Logout revokes the refresh session, not the short-lived access token.

    step(6, "GET", "/api/v1/auth/me")
    request("GET", "/api/v1/auth/me", token=access_token)

    step(7, "PATCH", "/api/v1/auth/me")
    request(
        "PATCH",
        "/api/v1/auth/me",
        token=access_token,
        json_body={"name": "PreMan Smoke Runner"},
    )

    step(8, "POST", "/api/v1/auth/forgot-password")
    forgot = request("POST", "/api/v1/auth/forgot-password", json_body={"email": email}).body
    reset_token = value(forgot, "reset_token")

    step(9, "POST", "/api/v1/auth/reset-password")
    request(
        "POST",
        "/api/v1/auth/reset-password",
        json_body={"reset_token": reset_token, "new_password": reset_password},
    )

    # Reset revokes old sessions; log back in before the authenticated operations.
    relogin = request(
        "POST",
        "/api/v1/auth/login",
        json_body={"email": email, "password": reset_password},
    ).body
    access_token = value(relogin, "access_token")

    step(10, "POST", "/api/v1/auth/change-password")
    request(
        "POST",
        "/api/v1/auth/change-password",
        token=access_token,
        json_body={
            "current_password": reset_password,
            "new_password": final_password,
        },
    )
    # The implementation may revoke sessions after a password change.
    relogin = request(
        "POST",
        "/api/v1/auth/login",
        json_body={"email": email, "password": final_password},
    ).body
    access_token = value(relogin, "access_token")

    step(11, "GET", "/api/v1/projects")
    request("GET", "/api/v1/projects", token=access_token)

    step(12, "POST", "/api/v1/projects")
    project = request(
        "POST",
        "/api/v1/projects",
        token=access_token,
        json_body={
            "name": f"Smoke Project {suffix}",
            "description": "Created by the all-operations live smoke test",
        },
        expected=(200, 201),
    ).body
    project_id = value(project, "id")

    step(13, "GET", f"/api/v1/projects/{project_id}")
    request("GET", f"/api/v1/projects/{project_id}", token=access_token)

    step(14, "PATCH", f"/api/v1/projects/{project_id}")
    request(
        "PATCH",
        f"/api/v1/projects/{project_id}",
        token=access_token,
        json_body={"description": "Updated by the live smoke test"},
    )

    step(16, "GET", f"/api/v1/projects/{project_id}/tasks")
    request("GET", f"/api/v1/projects/{project_id}/tasks", token=access_token)

    step(17, "POST", f"/api/v1/projects/{project_id}/tasks")
    task = request(
        "POST",
        f"/api/v1/projects/{project_id}/tasks",
        token=access_token,
        json_body={
            "title": f"Smoke Task {suffix}",
            "description": "Safe disposable task",
            "status": "todo",
            "priority": "high",
        },
        expected=(200, 201),
    ).body
    task_id = value(task, "id")

    step(18, "GET", f"/api/v1/tasks/{task_id}")
    request("GET", f"/api/v1/tasks/{task_id}", token=access_token)

    step(19, "PATCH", f"/api/v1/tasks/{task_id}")
    request(
        "PATCH",
        f"/api/v1/tasks/{task_id}",
        token=access_token,
        json_body={"status": "done", "priority": "medium"},
    )

    step(20, "DELETE", f"/api/v1/tasks/{task_id}")
    request(
        "DELETE",
        f"/api/v1/tasks/{task_id}",
        token=access_token,
        expected=(200, 204),
    )

    step(15, "DELETE", f"/api/v1/projects/{project_id}")
    request(
        "DELETE",
        f"/api/v1/projects/{project_id}",
        token=access_token,
        expected=(200, 204),
    )

    # A final deterministic login catches accidental seed/credential regressions.
    request(
        "POST",
        "/api/v1/auth/login",
        json_body={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )

    print(f"\nPASS: all 20 API operations succeeded against {BASE_URL}")
    return 0


if __name__ == "__main__":
    started = time.monotonic()
    try:
        result = main()
    except SmokeFailure as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"Completed in {time.monotonic() - started:.2f}s")
    raise SystemExit(result)
