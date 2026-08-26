#!/usr/bin/env python3
"""Exercise all 30 public mock CRUD operations through real HTTP.

The runner resets the mock database before and after the check. It never touches
the authenticated legacy project/task data.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
MOCK_PREFIX = "/api/v1/mock"
RESET_PATH = f"{MOCK_PREFIX}/reset"


@dataclass(frozen=True)
class Response:
    status: int
    body: Any


class SmokeFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class ResourceCase:
    resource: str
    create: dict[str, Any]
    replace: dict[str, Any]
    patch: dict[str, Any]

    @property
    def collection_path(self) -> str:
        return f"{MOCK_PREFIX}/{self.resource}"


def cases(suffix: str) -> tuple[ResourceCase, ...]:
    return (
        ResourceCase(
            "customers",
            {
                "name": "Live Smoke Customer",
                "email": f"mock-smoke-{suffix}@example.com",
                "phone": "+1-555-0199",
                "company": "Live Smoke Labs",
                "status": "active",
            },
            {
                "name": "Replaced Live Customer",
                "email": f"mock-smoke-put-{suffix}@example.com",
                "phone": "+1-555-0188",
                "company": "Replacement Smoke Labs",
                "status": "inactive",
            },
            {"name": "Patched Live Customer"},
        ),
        ResourceCase(
            "products",
            {
                "name": "Live Smoke Product",
                "sku": f"SMOKE-{suffix.upper()}",
                "description": "Disposable live-smoke product",
                "category": "Testing",
                "price_cents": 1999,
                "stock_quantity": 12,
                "active": True,
            },
            {
                "name": "Replaced Live Product",
                "sku": f"PUT-{suffix.upper()}",
                "description": "Complete live product replacement",
                "category": "Replacement",
                "price_cents": 2950,
                "stock_quantity": 7,
                "active": False,
            },
            {"price_cents": 2475},
        ),
        ResourceCase(
            "orders",
            {
                "customer_id": "cus_seed_001",
                "items": [{"product_id": "prd_seed_001", "quantity": 2}],
                "status": "pending",
                "shipping_address": "100 Live Smoke Way, Test City, CA 90001",
                "notes": "Disposable live-smoke order",
            },
            {
                "customer_id": "cus_seed_002",
                "items": [{"product_id": "prd_seed_002", "quantity": 4}],
                "status": "paid",
                "shipping_address": "200 Replacement Avenue, Test City, CA 90002",
                "notes": "Complete live order replacement",
            },
            {"status": "shipped"},
        ),
        ResourceCase(
            "tickets",
            {
                "customer_id": "cus_seed_001",
                "subject": "Live smoke support ticket",
                "description": "Disposable live-smoke request",
                "priority": "high",
                "status": "open",
                "assignee": "Live Smoke Agent",
            },
            {
                "customer_id": "cus_seed_002",
                "subject": "Replaced live support ticket",
                "description": "Complete live ticket replacement",
                "priority": "low",
                "status": "in_progress",
                "assignee": "Replacement Smoke Agent",
            },
            {"status": "resolved"},
        ),
        ResourceCase(
            "reviews",
            {
                "customer_id": "cus_seed_001",
                "product_id": "prd_seed_001",
                "rating": 4,
                "title": "Live smoke review",
                "body": "Created by the live mock smoke runner",
            },
            {
                "customer_id": "cus_seed_002",
                "product_id": "prd_seed_002",
                "rating": 3,
                "title": "Replacement smoke review",
                "body": "Complete live review replacement",
            },
            {"rating": 5},
        ),
    )


def request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    expected: int | tuple[int, ...] = 200,
) -> Response:
    headers = {"accept": "application/json"}
    data = None
    if json_body is not None:
        headers["content-type"] = "application/json"
        data = json.dumps(json_body).encode()
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as raw:
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
    return Response(status, body)


def assert_fields(body: Any, expected: dict[str, Any], context: str) -> None:
    if not isinstance(body, dict):
        raise SmokeFailure(f"{context} did not return an object: {body!r}")
    for field, value in expected.items():
        if body.get(field) != value:
            raise SmokeFailure(
                f"{context} returned {field}={body.get(field)!r}, expected {value!r}"
            )


def expected_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for resource in ("customers", "products", "orders", "tickets", "reviews"):
        collection = f"{MOCK_PREFIX}/{resource}"
        item = f"{collection}/{{item_id}}"
        operations.update(
            {
                ("GET", collection),
                ("POST", collection),
                ("GET", item),
                ("PUT", item),
                ("PATCH", item),
                ("DELETE", item),
            }
        )
    return operations


def verify_discovery_surfaces() -> None:
    document = request("GET", "/mock-openapi.json").body
    if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):
        raise SmokeFailure("GET /mock-openapi.json did not return an OpenAPI document")
    operations = {
        (method.upper(), path)
        for path, path_item in document["paths"].items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if operations != expected_operations():
        raise SmokeFailure(
            f"Expected the exact 30-operation mock contract, found {len(operations)} operations"
        )
    action_words = {
        ("GET", False): "list",
        ("POST", False): "create",
        ("GET", True): "get",
        ("PUT", True): "replace",
        ("PATCH", True): "update",
        ("DELETE", True): "delete",
    }
    for method, path in operations:
        resource = path.split("/")[4]
        is_item = "{item_id}" in path
        operation = document["paths"][path][method.lower()]
        if operation.get("tags") != [f"Mock {resource.title()}"]:
            raise SmokeFailure(f"{method} {path} does not have its expected resource label")
        summary = str(operation.get("summary", "")).lower()
        if action_words[(method, is_item)] not in summary:
            raise SmokeFailure(f"{method} {path} does not have a clear action summary")

    ui = request("GET", "/test-ui").body
    if not isinstance(ui, str):
        raise SmokeFailure("GET /test-ui did not return HTML")
    for resource in ("customers", "products", "orders", "tickets", "reviews"):
        if resource not in ui.lower():
            raise SmokeFailure(f"The browser test UI does not label {resource}")


def step(number: int, method: str, path: str) -> None:
    print(f"[mock operation {number:02d}] {method:<6} {path}")


def main() -> int:
    suffix = uuid4().hex[:12]
    operation_number = 0
    verify_discovery_surfaces()
    request("POST", RESET_PATH)

    try:
        for case in cases(suffix):
            operation_number += 1
            step(operation_number, "GET", case.collection_path)
            before = request("GET", f"{case.collection_path}?limit=100&offset=0").body
            if not isinstance(before, dict) or not isinstance(before.get("total"), int):
                raise SmokeFailure(f"GET {case.collection_path} returned an invalid list envelope")

            operation_number += 1
            step(operation_number, "POST", case.collection_path)
            created = request(
                "POST", case.collection_path, json_body=case.create, expected=201
            ).body
            assert_fields(created, case.create, f"POST {case.collection_path}")
            if not isinstance(created, dict) or not isinstance(created.get("id"), str):
                raise SmokeFailure(f"POST {case.collection_path} did not return a string id")
            item_id = created["id"]
            item_path = f"{case.collection_path}/{item_id}"

            operation_number += 1
            step(operation_number, "GET", item_path)
            fetched = request("GET", item_path).body
            if fetched != created:
                raise SmokeFailure(f"GET {item_path} did not return the created record")

            operation_number += 1
            step(operation_number, "PUT", item_path)
            replaced = request("PUT", item_path, json_body=case.replace).body
            assert_fields(replaced, case.replace, f"PUT {item_path}")

            operation_number += 1
            step(operation_number, "PATCH", item_path)
            patched = request("PATCH", item_path, json_body=case.patch).body
            assert_fields(patched, case.patch, f"PATCH {item_path}")

            operation_number += 1
            step(operation_number, "DELETE", item_path)
            request("DELETE", item_path, expected=204)
            request("GET", item_path, expected=404)

        if operation_number != 30:
            raise SmokeFailure(f"Expected to exercise 30 operations, exercised {operation_number}")
    finally:
        request("POST", RESET_PATH)

    print(
        f"PASS: {BASE_URL} exposes the exact labeled mock contract and all "
        "30 CRUD operations passed"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
