from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.mock_schema_catalog import (
    MOCK_SCHEMA_CATALOG_PATH,
    RESOURCE_MODELS,
    build_mock_schema_catalog,
)

MOCK_PREFIX = "/api/v1/mock"
RESET_PATH = f"{MOCK_PREFIX}/reset"
SEED_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "mock_db.json"
SCHEMA_CATALOG = json.loads(MOCK_SCHEMA_CATALOG_PATH.read_text())


def schema_example(resource: str, operation: str) -> dict[str, Any]:
    return SCHEMA_CATALOG["resources"][resource]["operations"][operation]["request_example"]


@dataclass(frozen=True)
class ResourceCase:
    resource: str
    create: dict[str, Any]
    replace: dict[str, Any]
    patch: dict[str, Any]
    stable_field: str
    invalid: dict[str, Any]

    @property
    def collection_path(self) -> str:
        return f"{MOCK_PREFIX}/{self.resource}"


RESOURCE_CASES = (
    ResourceCase(
        resource="customers",
        create=schema_example("customers", "create"),
        replace=schema_example("customers", "replace"),
        patch=schema_example("customers", "patch"),
        stable_field="email",
        invalid={
            "name": "Invalid Customer",
            "email": "not-an-email",
            "phone": "+1-555-0177",
            "company": "Invalid Test Labs",
            "status": "active",
        },
    ),
    ResourceCase(
        resource="products",
        create=schema_example("products", "create"),
        replace=schema_example("products", "replace"),
        patch=schema_example("products", "patch"),
        stable_field="sku",
        invalid={
            "name": "Invalid Product",
            "sku": "API-BAD-001",
            "description": "Negative prices are invalid",
            "category": "Testing",
            "price_cents": -1,
            "stock_quantity": 1,
            "active": True,
        },
    ),
    ResourceCase(
        resource="orders",
        create=schema_example("orders", "create"),
        replace=schema_example("orders", "replace"),
        patch=schema_example("orders", "patch"),
        stable_field="customer_id",
        invalid={
            "customer_id": "cus_seed_001",
            "items": [{"product_id": "prd_seed_001", "quantity": 0}],
            "status": "pending",
            "shipping_address": "100 Contract Test Way, Test City, CA 90001",
            "notes": "An item quantity of zero is invalid",
        },
    ),
    ResourceCase(
        resource="tickets",
        create=schema_example("tickets", "create"),
        replace=schema_example("tickets", "replace"),
        patch=schema_example("tickets", "patch"),
        stable_field="subject",
        invalid={
            "customer_id": "cus_seed_001",
            "subject": "Invalid priority ticket",
            "description": "Priority must be one of the documented values",
            "priority": "not-a-priority",
            "status": "open",
            "assignee": "Contract Test Agent",
        },
    ),
    ResourceCase(
        resource="reviews",
        create=schema_example("reviews", "create"),
        replace=schema_example("reviews", "replace"),
        patch=schema_example("reviews", "patch"),
        stable_field="body",
        invalid={
            "customer_id": "cus_seed_001",
            "product_id": "prd_seed_001",
            "rating": 6,
            "title": "Invalid rating review",
            "body": "Ratings cannot exceed five",
        },
    ),
)

RESOURCE_NAMES = tuple(case.resource for case in RESOURCE_CASES)
CASE_IDS = tuple(case.resource for case in RESOURCE_CASES)
CRUD_METHODS = {"get", "post", "put", "patch", "delete"}


def expected_mock_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for resource in RESOURCE_NAMES:
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


EXPECTED_MOCK_OPERATIONS = expected_mock_operations()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Reset the public mock store around every test for deterministic isolation."""

    with TestClient(app) as test_client:
        before = test_client.post(RESET_PATH)
        assert before.status_code == 200, before.text
        yield test_client
        after = test_client.post(RESET_PATH)
        assert after.status_code == 200, after.text


def collection_body(response) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"items", "total", "limit", "offset"} <= body.keys()
    assert isinstance(body["items"], list)
    assert body["total"] >= len(body["items"])
    return body


def assert_fields(body: dict[str, Any], expected: dict[str, Any]) -> None:
    for field, value in expected.items():
        assert body[field] == value


def assert_error(response, status: int, code: str | None = None) -> dict[str, Any]:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert isinstance(body["error"]["message"], str)
    if code is not None:
        assert body["error"]["code"] == code
    return body


def test_mock_seed_is_a_well_formed_json_database() -> None:
    assert SEED_PATH.is_file(), f"Missing mock JSON seed: {SEED_PATH}"
    database = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    assert set(database) == {"meta", *RESOURCE_NAMES}
    assert isinstance(database["meta"], dict)
    for case in RESOURCE_CASES:
        records = database[case.resource]
        assert isinstance(records, list) and records, f"{case.resource} needs seed records"
        ids = [record.get("id") for record in records]
        assert all(isinstance(item_id, str) and item_id for item_id in ids)
        assert len(ids) == len(set(ids)), f"{case.resource} seed IDs must be unique"
        for record in records:
            assert set(case.create) <= record.keys()


def test_mock_schema_catalog_is_current_and_examples_validate() -> None:
    assert MOCK_SCHEMA_CATALOG_PATH.is_file()
    assert SCHEMA_CATALOG == build_mock_schema_catalog()
    assert set(SCHEMA_CATALOG["resources"]) == set(RESOURCE_NAMES)

    for resource, models in RESOURCE_MODELS.items():
        operations = SCHEMA_CATALOG["resources"][resource]["operations"]
        assert set(operations) == {"list", "create", "get", "replace", "patch", "delete"}
        for purpose in ("create", "replace", "patch"):
            example = operations[purpose]["request_example"]
            validated = models[purpose].model_validate(example)
            assert validated.model_dump(mode="json", exclude_unset=True) == example


def test_mock_schema_catalog_is_downloadable(client: TestClient) -> None:
    response = client.get("/mock-schemas.json")
    assert response.status_code == 200, response.text
    assert response.json() == SCHEMA_CATALOG


def test_reset_restores_every_collection_from_the_json_seed(client: TestClient) -> None:
    database = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    created = client.post(
        f"{MOCK_PREFIX}/customers",
        json={
            **RESOURCE_CASES[0].create,
            "email": f"reset-{uuid4().hex[:10]}@example.com",
        },
    )
    assert created.status_code == 201, created.text
    created_id = created.json()["id"]

    reset = client.post(RESET_PATH)
    assert reset.status_code == 200, reset.text
    assert any(word in reset.json()["message"].lower() for word in ("reset", "restor"))

    for resource in RESOURCE_NAMES:
        body = collection_body(client.get(f"{MOCK_PREFIX}/{resource}?limit=100&offset=0"))
        assert body["total"] == len(database[resource])
        assert {record["id"] for record in body["items"]} == {
            record["id"] for record in database[resource]
        }
    assert_error(client.get(f"{MOCK_PREFIX}/customers/{created_id}"), 404, "customer_not_found")


@pytest.mark.parametrize("case", RESOURCE_CASES, ids=CASE_IDS)
def test_complete_crud_lifecycle_for_each_mock_resource(
    client: TestClient, case: ResourceCase
) -> None:
    initial = collection_body(client.get(f"{case.collection_path}?limit=100&offset=0"))
    initial_total = initial["total"]

    create_payload = dict(case.create)
    if case.resource == "customers":
        create_payload["email"] = f"crud-{uuid4().hex[:10]}@example.com"
    if case.resource == "products":
        create_payload["sku"] = f"CRUD-{uuid4().hex[:10].upper()}"

    created_response = client.post(case.collection_path, json=create_payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    item_id = created["id"]
    assert isinstance(item_id, str) and item_id
    assert_fields(created, create_payload)

    listed = collection_body(client.get(f"{case.collection_path}?limit=100&offset=0"))
    assert listed["total"] == initial_total + 1
    assert item_id in {item["id"] for item in listed["items"]}

    fetched = client.get(f"{case.collection_path}/{item_id}")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json() == created

    replacement_payload = dict(case.replace)
    if case.resource == "customers":
        replacement_payload["email"] = f"put-{uuid4().hex[:10]}@example.com"
    if case.resource == "products":
        replacement_payload["sku"] = f"PUT-{uuid4().hex[:10].upper()}"

    replaced_response = client.put(f"{case.collection_path}/{item_id}", json=replacement_payload)
    assert replaced_response.status_code == 200, replaced_response.text
    replaced = replaced_response.json()
    assert replaced["id"] == item_id
    assert_fields(replaced, replacement_payload)

    patched_response = client.patch(f"{case.collection_path}/{item_id}", json=case.patch)
    assert patched_response.status_code == 200, patched_response.text
    patched = patched_response.json()
    assert patched["id"] == item_id
    assert_fields(patched, case.patch)
    assert patched[case.stable_field] == replacement_payload[case.stable_field]

    deleted = client.delete(f"{case.collection_path}/{item_id}")
    assert deleted.status_code == 204, deleted.text
    assert not deleted.content

    final_list = collection_body(client.get(f"{case.collection_path}?limit=100&offset=0"))
    assert final_list["total"] == initial_total
    assert item_id not in {item["id"] for item in final_list["items"]}
    assert_error(
        client.get(f"{case.collection_path}/{item_id}"),
        404,
        f"{case.resource.removesuffix('s')}_not_found",
    )


@pytest.mark.parametrize("case", RESOURCE_CASES, ids=CASE_IDS)
def test_mock_payload_validation_is_resource_specific(
    client: TestClient, case: ResourceCase
) -> None:
    assert_error(client.post(case.collection_path, json=case.invalid), 422, "validation_error")

    # PUT is a complete replacement, while PATCH only accepts documented fields.
    missing_id = f"validation-{uuid4().hex}"
    incomplete = client.put(f"{case.collection_path}/{missing_id}", json=case.patch)
    assert_error(incomplete, 422, "validation_error")
    unexpected = client.patch(
        f"{case.collection_path}/{missing_id}",
        json={"definitely_not_a_documented_field": True},
    )
    assert_error(unexpected, 422, "validation_error")


@pytest.mark.parametrize("case", RESOURCE_CASES, ids=CASE_IDS)
def test_patch_rejects_null_without_corrupting_the_stored_record(
    client: TestClient, case: ResourceCase
) -> None:
    database = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    item_id = database[case.resource][0]["id"]
    item_path = f"{case.collection_path}/{item_id}"
    before = client.get(item_path)
    assert before.status_code == 200, before.text

    rejected = client.patch(item_path, json={case.stable_field: None})
    assert_error(rejected, 422, "validation_error")

    after = client.get(item_path)
    assert after.status_code == 200, after.text
    assert after.json() == before.json()


@pytest.mark.parametrize(
    ("resource", "item_id", "code"),
    (
        ("customers", "cus_seed_001", "customer_in_use"),
        ("products", "prd_seed_001", "product_in_use"),
    ),
)
def test_delete_rejects_records_that_are_still_referenced(
    client: TestClient, resource: str, item_id: str, code: str
) -> None:
    rejected = client.delete(f"{MOCK_PREFIX}/{resource}/{item_id}")
    body = assert_error(rejected, 409, code)
    assert body["error"]["details"]["references"]

    preserved = client.get(f"{MOCK_PREFIX}/{resource}/{item_id}")
    assert preserved.status_code == 200, preserved.text


@pytest.mark.parametrize("case", RESOURCE_CASES, ids=CASE_IDS)
def test_unknown_mock_items_return_consistent_404_errors(
    client: TestClient, case: ResourceCase
) -> None:
    missing_id = f"missing-{uuid4().hex}"
    item_path = f"{case.collection_path}/{missing_id}"

    code = f"{case.resource.removesuffix('s')}_not_found"
    assert_error(client.get(item_path), 404, code)
    assert_error(client.put(item_path, json=case.replace), 404, code)
    assert_error(client.patch(item_path, json=case.patch), 404, code)
    assert_error(client.delete(item_path), 404, code)


def test_mock_openapi_contains_exactly_30_labeled_crud_operations(
    client: TestClient,
) -> None:
    response = client.get("/mock-openapi.json")
    assert response.status_code == 200, response.text
    document = response.json()

    operations = {
        (method.upper(), path)
        for path, path_item in document["paths"].items()
        for method in path_item
        if method.lower() in CRUD_METHODS
    }
    assert operations == EXPECTED_MOCK_OPERATIONS
    assert len(operations) == 30
    assert RESET_PATH not in document["paths"]

    operation_ids: list[str] = []
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
        assert operation["tags"] == [f"Mock {resource.title()}"]
        assert action_words[(method, is_item)] in operation["summary"].lower()
        assert resource.removesuffix("s") in operation["summary"].lower()
        assert operation["description"].strip()
        assert "422" in operation["responses"]
        if is_item:
            assert "404" in operation["responses"]
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            assert "409" in operation["responses"]
        for status_code, error_response in operation["responses"].items():
            if status_code in {"404", "409", "422"}:
                schema = error_response["content"]["application/json"]["schema"]
                assert schema == {"$ref": "#/components/schemas/ErrorResponse"}
        operation_ids.append(operation["operationId"])
    assert len(operation_ids) == len(set(operation_ids))


def test_main_openapi_keeps_legacy_and_mock_routes_but_hides_reset(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    assert "/health" in document["paths"]
    assert "/api/v1/auth/login" in document["paths"]
    assert "/api/v1/projects" in document["paths"]
    for _, path in EXPECTED_MOCK_OPERATIONS:
        assert path in document["paths"]
    assert RESET_PATH not in document["paths"]


def test_browser_test_ui_exposes_every_mock_resource(client: TestClient) -> None:
    response = client.get("/test-ui")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/html")
    html = response.text.lower()

    assert "/mock-openapi.json" in html
    assert "/mock-schemas.json" in html
    assert RESET_PATH in html
    for resource in RESOURCE_NAMES:
        assert resource in html
        assert f"{MOCK_PREFIX}/{resource}" in html
    for method in ("get", "post", "put", "patch", "delete"):
        assert method in html
