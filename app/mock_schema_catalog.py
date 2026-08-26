from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.mock_schemas import (
    CustomerCreate,
    CustomerReplace,
    CustomerResponse,
    CustomerUpdate,
    MockPage,
    OrderCreate,
    OrderReplace,
    OrderResponse,
    OrderUpdate,
    ProductCreate,
    ProductReplace,
    ProductResponse,
    ProductUpdate,
    ReviewCreate,
    ReviewReplace,
    ReviewResponse,
    ReviewUpdate,
    TicketCreate,
    TicketReplace,
    TicketResponse,
    TicketUpdate,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
SEED_PATH = DATA_DIR / "mock_db.json"
MOCK_SCHEMA_CATALOG_PATH = DATA_DIR / "mock_api_schemas.json"

RESOURCE_MODELS: dict[str, dict[str, type[BaseModel]]] = {
    "customers": {
        "create": CustomerCreate,
        "replace": CustomerReplace,
        "patch": CustomerUpdate,
        "response": CustomerResponse,
        "page": MockPage[CustomerResponse],
    },
    "products": {
        "create": ProductCreate,
        "replace": ProductReplace,
        "patch": ProductUpdate,
        "response": ProductResponse,
        "page": MockPage[ProductResponse],
    },
    "orders": {
        "create": OrderCreate,
        "replace": OrderReplace,
        "patch": OrderUpdate,
        "response": OrderResponse,
        "page": MockPage[OrderResponse],
    },
    "tickets": {
        "create": TicketCreate,
        "replace": TicketReplace,
        "patch": TicketUpdate,
        "response": TicketResponse,
        "page": MockPage[TicketResponse],
    },
    "reviews": {
        "create": ReviewCreate,
        "replace": ReviewReplace,
        "patch": ReviewUpdate,
        "response": ReviewResponse,
        "page": MockPage[ReviewResponse],
    },
}

REQUEST_EXAMPLES: dict[str, dict[str, dict[str, Any]]] = {
    "customers": {
        "create": {
            "name": "API Test Customer",
            "email": "api-test-customer@example.com",
            "phone": "+1-555-0199",
            "company": "Contract Test Labs",
            "status": "active",
        },
        "replace": {
            "name": "Replacement Customer",
            "email": "replacement-customer@example.com",
            "phone": "+1-555-0188",
            "company": "Replacement Test Labs",
            "status": "inactive",
        },
        "patch": {"name": "Patched Customer"},
    },
    "products": {
        "create": {
            "name": "API Test Product",
            "sku": "API-TEST-001",
            "description": "Disposable product created by a contract test",
            "category": "Testing",
            "price_cents": 1999,
            "stock_quantity": 12,
            "active": True,
        },
        "replace": {
            "name": "Replacement Product",
            "sku": "API-TEST-002",
            "description": "Complete product replacement",
            "category": "Replacement",
            "price_cents": 2950,
            "stock_quantity": 7,
            "active": False,
        },
        "patch": {"price_cents": 2475},
    },
    "orders": {
        "create": {
            "customer_id": "cus_seed_001",
            "items": [{"product_id": "prd_seed_001", "quantity": 2}],
            "status": "pending",
            "shipping_address": "100 Contract Test Way, Test City, CA 90001",
            "notes": "Disposable order created by a contract test",
        },
        "replace": {
            "customer_id": "cus_seed_002",
            "items": [{"product_id": "prd_seed_002", "quantity": 4}],
            "status": "paid",
            "shipping_address": "200 Replacement Avenue, Test City, CA 90002",
            "notes": "Complete order replacement",
        },
        "patch": {"status": "shipped"},
    },
    "tickets": {
        "create": {
            "customer_id": "cus_seed_001",
            "subject": "API contract test ticket",
            "description": "Disposable support request",
            "priority": "high",
            "status": "open",
            "assignee": "Contract Test Agent",
        },
        "replace": {
            "customer_id": "cus_seed_002",
            "subject": "Replacement support ticket",
            "description": "Complete ticket replacement",
            "priority": "low",
            "status": "in_progress",
            "assignee": "Replacement Test Agent",
        },
        "patch": {"status": "resolved"},
    },
    "reviews": {
        "create": {
            "customer_id": "cus_seed_001",
            "product_id": "prd_seed_001",
            "rating": 4,
            "title": "Contract test review",
            "body": "Created by the API contract test",
        },
        "replace": {
            "customer_id": "cus_seed_002",
            "product_id": "prd_seed_002",
            "rating": 3,
            "title": "Replacement test review",
            "body": "Complete review replacement",
        },
        "patch": {"rating": 5},
    },
}


def _add_definition(
    definitions: dict[str, Any], alias: str, model: type[BaseModel]
) -> dict[str, str]:
    schema = model.model_json_schema(ref_template="#/$defs/{model}")
    nested_definitions = schema.pop("$defs", {})
    for name, definition in nested_definitions.items():
        existing = definitions.get(name)
        if existing is not None and existing != definition:
            raise ValueError(f"Conflicting JSON Schema definition: {name}")
        definitions[name] = definition
    definitions[alias] = schema
    return {"$ref": f"#/$defs/{alias}"}


def build_mock_schema_catalog() -> dict[str, Any]:
    seed = json.loads(SEED_PATH.read_text())
    definitions: dict[str, Any] = {}
    resources: dict[str, Any] = {}

    for resource, models in RESOURCE_MODELS.items():
        singular = resource.removesuffix("s")
        aliases = {
            "create": f"{singular.title()}Create",
            "replace": f"{singular.title()}Replace",
            "patch": f"{singular.title()}Patch",
            "response": f"{singular.title()}Response",
            "page": f"{singular.title()}Page",
        }
        refs = {
            purpose: _add_definition(definitions, aliases[purpose], model)
            for purpose, model in models.items()
        }
        collection_path = f"/api/v1/mock/{resource}"
        item_path = f"{collection_path}/{{item_id}}"
        response_example = seed[resource][0]
        page_example = {
            "items": seed[resource][:2],
            "total": len(seed[resource]),
            "limit": 20,
            "offset": 0,
        }
        examples = REQUEST_EXAMPLES[resource]

        resources[resource] = {
            "description": f"Reusable schemas and fixtures for mock {resource} tests.",
            "collection_path": collection_path,
            "item_path": item_path,
            "operations": {
                "list": {
                    "method": "GET",
                    "path": collection_path,
                    "expected_status": 200,
                    "response_schema": refs["page"],
                    "response_example": page_example,
                },
                "create": {
                    "method": "POST",
                    "path": collection_path,
                    "expected_status": 201,
                    "request_schema": refs["create"],
                    "request_example": examples["create"],
                    "response_schema": refs["response"],
                    "response_example": response_example,
                },
                "get": {
                    "method": "GET",
                    "path": item_path,
                    "expected_status": 200,
                    "response_schema": refs["response"],
                    "response_example": response_example,
                },
                "replace": {
                    "method": "PUT",
                    "path": item_path,
                    "expected_status": 200,
                    "request_schema": refs["replace"],
                    "request_example": examples["replace"],
                    "response_schema": refs["response"],
                    "response_example": response_example,
                },
                "patch": {
                    "method": "PATCH",
                    "path": item_path,
                    "expected_status": 200,
                    "request_schema": refs["patch"],
                    "request_example": examples["patch"],
                    "response_schema": refs["response"],
                    "response_example": response_example,
                },
                "delete": {
                    "method": "DELETE",
                    "path": item_path,
                    "expected_status": 204,
                    "response_schema": None,
                    "response_example": None,
                },
            },
        }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "schema_version": 1,
        "title": "PreMan Mock API Test Schema Catalog",
        "description": (
            "Machine-readable JSON Schemas, request fixtures, and response examples for "
            "all 30 hosted mock CRUD operations."
        ),
        "base_path": "/api/v1/mock",
        "resources": resources,
        "$defs": definitions,
    }


def load_mock_schema_catalog() -> dict[str, Any]:
    return json.loads(MOCK_SCHEMA_CATALOG_PATH.read_text())
