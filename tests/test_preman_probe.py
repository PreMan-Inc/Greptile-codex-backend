"""The probe endpoints' contracts are wrong on purpose.

These tests exist so each mismatch reads as a fixture rather than an oversight,
and so the day one is repaired is a visible change here rather than a silent
one. They assert the drift is present and that nothing else about the endpoint
is surprising — deliberately not that ``total_cents`` or a stringified
``amount_refunded`` is correct, because neither is.

The two drifts are different on purpose: ``order-total`` drops a documented
field, ``refund-status`` keeps every field but ships one as the wrong type. A
consumer hits them differently, and so does anything checking the response
against the published schema. See app/routers/preman_probe.py.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

PATH = "/api/v1/preman-probe/order-total"
REFUND_PATH = "/api/v1/preman-probe/refund-status"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_the_probe_answers_and_says_which_order_it_is_about(client: TestClient) -> None:
    response = client.get(PATH)
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == "ord-4471"
    assert body["currency"] == "GBP"


def test_the_published_schema_still_promises_a_total(client: TestClient) -> None:
    """The half of the mismatch a consumer reads before calling."""
    schema = client.get("/openapi.json").json()["components"]["schemas"]["OrderTotal"]
    assert set(schema["properties"]) == {"order_id", "currency", "total"}


def test_the_response_does_not_carry_the_total_it_promised(client: TestClient) -> None:
    """The other half: this is the drift PreMan is meant to find and repair.

    When it is repaired, this test fails — which is the point. Delete it and the
    fixture together rather than relaxing it.
    """
    body = client.get(PATH).json()
    assert "total" not in body
    assert body["total_cents"] == 4200


def test_the_probe_is_read_only(client: TestClient) -> None:
    """Whatever else it does, it must not offer a way to change anything."""
    paths = client.get("/openapi.json").json()["paths"][PATH]
    assert set(paths) == {"get"}


def test_the_refund_probe_answers_with_every_documented_field(client: TestClient) -> None:
    """Unlike the order probe, nothing here is missing — only mistyped."""
    response = client.get(REFUND_PATH)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"order_id", "state", "amount_refunded"}
    assert body["order_id"] == "ord-4471"
    assert body["state"] == "settled"


def test_the_published_schema_types_the_refund_as_a_number(client: TestClient) -> None:
    """The half of the mismatch a consumer reads before calling."""
    schema = client.get("/openapi.json").json()["components"]["schemas"]["RefundStatus"]
    assert schema["properties"]["amount_refunded"]["type"] == "number"


def test_the_refund_amount_is_served_as_a_string(client: TestClient) -> None:
    """The other half: the drift PreMan is meant to find and repair.

    When it is repaired, this test fails — which is the point. Delete it and the
    fixture together rather than relaxing it.
    """
    amount = client.get(REFUND_PATH).json()["amount_refunded"]
    assert isinstance(amount, str)
    assert amount == "42.00"


def test_the_refund_probe_is_read_only(client: TestClient) -> None:
    """Whatever else it does, it must not offer a way to change anything."""
    paths = client.get("/openapi.json").json()["paths"][REFUND_PATH]
    assert set(paths) == {"get"}
