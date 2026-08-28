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

No drift here is pinned by a test any more. A test asserting the response omits
``total``, or ships ``amount_refunded`` as a string, fails the moment that
endpoint is repaired -- so the repository rejects the very fix the fixture
exists to prove, and one red test blocks every other repair with it. That is
not a fixture, it is a trap.

What each endpoint publishes is still asserted, so a repair stays visible here:
it turns the contract and the response from a mismatch into agreement.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

PATH = "/api/v1/preman-probe/order-total"
REFUND_PATH = "/api/v1/preman-probe/refund-status"
DISCOUNT_PATH = "/api/v1/preman-probe/discount"


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
    assert set(schema["properties"]) == {"order_id", "currency", "total", "paid"}


def test_the_probe_is_read_only(client: TestClient) -> None:
    """Whatever else it does, it must not offer a way to change anything."""
    paths = client.get("/openapi.json").json()["paths"][PATH]
    assert set(paths) == {"get"}


def test_the_refund_probe_answers_only_fields_it_documents(client: TestClient) -> None:
    """Every key served is published, and the identifying ones are always there.

    Deliberately a subset check rather than an equality one. The endpoint may
    publish a field it does not yet serve -- that is the drift -- so pinning the
    exact key set would fail the moment such a field is repaired into the
    response, and the repository would reject the fix. Undocumented keys are
    still caught, which is the direction that harms a consumer.
    """
    response = client.get(REFUND_PATH)
    assert response.status_code == 200
    body = response.json()
    documented = set(
        client.get("/openapi.json").json()["components"]["schemas"]["RefundStatus"][
            "properties"
        ]
    )
    assert {"order_id", "state"} <= set(body) <= documented
    assert body["order_id"] == "ord-4471"
    assert body["state"] == "settled"


def test_the_published_schema_types_the_refund_as_a_number(client: TestClient) -> None:
    """The half of the mismatch a consumer reads before calling."""
    schema = client.get("/openapi.json").json()["components"]["schemas"]["RefundStatus"]
    assert schema["properties"]["amount_refunded"]["type"] == "number"


def test_the_refund_probe_is_read_only(client: TestClient) -> None:
    """Whatever else it does, it must not offer a way to change anything."""
    paths = client.get("/openapi.json").json()["paths"][REFUND_PATH]
    assert set(paths) == {"get"}


def test_the_discount_probe_answers_correctly_inside_the_documented_range(
    client: TestClient,
) -> None:
    """In range there is no bug at all — only the boundary is unguarded."""
    body = client.get(DISCOUNT_PATH, params={"percent_off": 15}).json()
    assert body["order_id"] == "ord-4471"
    assert body["percent_off"] == 15
    assert body["total"] == 35.7


def test_the_published_contract_bounds_the_percentage_and_documents_a_422(
    client: TestClient,
) -> None:
    """The half of the mismatch a consumer reads before calling."""
    document = client.get("/openapi.json").json()
    schema = document["components"]["schemas"]["DiscountQuote"]["properties"]["percent_off"]
    assert schema["minimum"] == 0
    assert schema["maximum"] == 100
    assert "422" in document["paths"][DISCOUNT_PATH]["get"]["responses"]


def test_the_discount_probe_is_read_only(client: TestClient) -> None:
    """Whatever else it does, it must not offer a way to change anything."""
    paths = client.get("/openapi.json").json()["paths"][DISCOUNT_PATH]
    assert set(paths) == {"get"}
