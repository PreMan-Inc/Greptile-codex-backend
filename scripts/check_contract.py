#!/usr/bin/env python3
"""Fail CI when the preserved legacy contract drifts.

The counts below are derived, not written down. They used to be a literal 23
that meant "the legacy contract plus however many fixtures exist today", so
adding a fixture failed this check in a way that read like real drift.
"""

from app.main import app

LEGACY_OPERATIONS = {
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

# Fixtures for PreMan's own loops, not part of the preserved contract. Listed
# so the drift they carry stays inside their own handlers rather than tripping
# this check. See app/routers/preman_probe.py.
PROBE_OPERATIONS = {
    ("GET", "/api/v1/preman-probe/order-total"),
    ("GET", "/api/v1/preman-probe/refund-status"),
    ("GET", "/api/v1/preman-probe/shipping-estimate"),
}

EXPECTED_OPERATIONS = LEGACY_OPERATIONS | PROBE_OPERATIONS


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
            f"Legacy API contract drifted from {len(LEGACY_OPERATIONS)} operations "
            f"plus {len(PROBE_OPERATIONS)} probe fixtures. "
            f"Missing: {missing or 'none'}; unexpected: {unexpected or 'none'}"
        )
    print(
        f"PASS: OpenAPI exposes the preserved {len(LEGACY_OPERATIONS)}-operation "
        f"contract and {len(PROBE_OPERATIONS)} probe fixtures"
    )


if __name__ == "__main__":
    main()
