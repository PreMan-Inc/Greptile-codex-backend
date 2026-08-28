#!/usr/bin/env python3
"""Non-mutating health and contract checks for the public demo service."""

from __future__ import annotations

import json
import os
from urllib.request import urlopen

BASE_URL = (
    os.environ.get("BASE_URL")
    or "https://xixoo2yundjxsbdwl3iw2eg5hi0ckwfu.lambda-url.us-east-1.on.aws"
).rstrip("/")


def get_json(path: str) -> dict[str, object]:
    with urlopen(f"{BASE_URL}{path}", timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"GET {path} returned HTTP {response.status}")
        return json.load(response)


def get_text(path: str) -> str:
    with urlopen(f"{BASE_URL}{path}", timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"GET {path} returned HTTP {response.status}")
        return response.read().decode()


def main() -> None:
    health = get_json("/health")
    ready = get_json("/ready")
    document = get_json("/openapi.json")
    mock_document = get_json("/mock-openapi.json")
    mock_schemas = get_json("/mock-schemas.json")
    mock_customers = get_json("/api/v1/mock/customers?limit=1")
    test_ui = get_text("/test-ui")
    paths = document.get("paths", {})
    operations = {
        (method.upper(), path)
        for path, path_item in paths.items()
        if path == "/health"
        or (path.startswith("/api/v1/") and not path.startswith("/api/v1/mock/"))
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    mock_operations = {
        (method.upper(), path)
        for path, path_item in mock_document.get("paths", {}).items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if health.get("status") != "ok" or ready.get("status") != "ready":
        raise RuntimeError("The demo service is not healthy and ready")
    # The probe fixtures live under /api/v1/ and so match the legacy filter
    # above, but they are not part of the preserved contract. Counting them as
    # legacy would fail this check the first time a deploy carries one, which is
    # exactly when the service is healthy. Separate them, then hold the legacy
    # count that actually matters.
    probe_operations = {op for op in operations if op[1].startswith("/api/v1/preman-probe/")}
    legacy_operations = operations - probe_operations
    if len(legacy_operations) != 22:
        raise RuntimeError(
            f"Expected 22 legacy operations, found {len(legacy_operations)} "
            f"(plus {len(probe_operations)} probe fixtures)"
        )
    if len(mock_operations) != 30:
        raise RuntimeError(f"Expected 30 mock operations, found {len(mock_operations)}")
    if set(mock_schemas.get("resources", {})) != {
        "customers",
        "products",
        "orders",
        "tickets",
        "reviews",
    }:
        raise RuntimeError("The hosted mock schema fixture catalog is unavailable or malformed")
    if not isinstance(mock_customers.get("items"), list):
        raise TypeError("The hosted JSON mock store is unavailable or malformed")
    if "Mock API Workbench" not in test_ui:
        raise RuntimeError("The browser test UI is unavailable or malformed")
    print(
        f"PASS: {BASE_URL} is healthy and exposes 22 legacy + 30 mock operations "
        "with the browser test UI and reusable schema fixtures"
    )


if __name__ == "__main__":
    main()
