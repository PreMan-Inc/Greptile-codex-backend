#!/usr/bin/env python3
"""Non-mutating health and contract check for the public demo service."""

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


def main() -> None:
    health = get_json("/health")
    ready = get_json("/ready")
    document = get_json("/openapi.json")
    paths = document.get("paths", {})
    operations = {
        (method.upper(), path)
        for path, path_item in paths.items()
        if path == "/health" or path.startswith("/api/v1/")
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if health.get("status") != "ok" or ready.get("status") != "ready":
        raise RuntimeError("The demo service is not healthy and ready")
    if len(operations) != 22:
        raise RuntimeError(f"Expected 22 product operations, found {len(operations)}")
    print(f"PASS: {BASE_URL} is healthy, ready, and exposes exactly 22 operations")


if __name__ == "__main__":
    main()
