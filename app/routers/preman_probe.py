"""Fixtures for PreMan's own loops: two wrong contracts, and a new route.

PreMan is meant to notice when an API stops matching the shape it publishes,
repair it, and open a pull request. Proving that end to end needs a real
mismatch on a real deployment, and inventing one by hand each time is slower
than keeping one here.

``shipping_estimate`` below serves the other half: an endpoint introduced by a
push, which is what proves the pre-push hook tests a route on the same push
that adds it rather than only after the next repository scan.

The drifts are deliberately different shapes, because they fail differently.
``order_total`` renames a field: the schema promises ``total``, the handler
returns ``total_cents``, and a consumer reading ``total`` gets nothing — a
missing-field failure. ``refund_status`` keeps every documented name but ships
``amount_refunded`` as a string where the schema types it as a number — a type
failure, which is what a consumer doing arithmetic on it trips over. Both are
drifts on the way out.

``discount`` is the one on the way in: the contract bounds ``percent_off`` to
0–100 and documents a 422, and the handler enforces neither, so invalid input
is accepted rather than rejected. That is a stronger repair signal than a
broken response — a wrong answer is arguable, an unenforced documented
constraint is not — and it is the shape most real APIs get wrong first.

Returning a ``JSONResponse`` is what makes either observable: FastAPI validates
a returned model against ``response_model`` and would otherwise correct the very
thing being tested, and Pydantic would quietly coerce ``"42.00"`` to ``42.0``.

Read-only, no stored state, and it answers the same way every time, so the only
thing it can break is a caller expecting the published contract. To retire the
fixture, delete this module and its line in ``app.main``.

A green contract check against these four routes therefore means the check is
not reading the response, not that the routes are correct.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["preman-probe"])


class OrderTotal(BaseModel):
    """What the endpoint promises. The handler no longer honours ``total``."""

    order_id: str = Field(
        examples=["ord-4471"], description="Identifier of the order being totalled."
    )
    currency: str = Field(
        examples=["GBP"],
        description="ISO 4217 code that `total` is denominated in.",
    )
    total: float = Field(
        examples=[42.0],
        description="Order total, in whole currency units rather than minor units.",
    )
    paid: bool = Field(
        examples=[True],
        description="Whether the order has been settled in full, not in part.",
    )


@router.get(
    "/preman-probe/order-total",
    response_model=OrderTotal,
    summary="An order total, in the shape the schema promises",
    description=(
        "A fixture for PreMan's self-healing loop. The published schema names "
        "`total`; the handler returns `total_cents`. The repair is to serve the "
        "documented field again."
    ),
)
def order_total() -> JSONResponse:
    return JSONResponse(
        {
            "order_id": "ord-4471",
            "currency": "GBP",
            "total": 42.0,
            "paid": True,
        }
    )


class RefundStatus(BaseModel):
    """What a consumer reads before calling. The handler ships the wrong type."""

    order_id: str = Field(examples=["ord-4471"])
    state: str = Field(examples=["settled"])
    amount_refunded: float = Field(
        examples=[42.0],
        description="Amount returned to the customer, in currency units.",
    )


@router.get(
    "/preman-probe/refund-status",
    response_model=RefundStatus,
    summary="A refund's state and the amount returned",
    description=(
        "A fixture for PreMan's self-healing loop. The published schema types "
        "`amount_refunded` as a number; the handler serialises it as a string. "
        "The repair is to serve the documented type again."
    ),
)
def refund_status() -> JSONResponse:
    return JSONResponse(
        {
            "order_id": "ord-4471",
            "state": "settled",
            # The drift under test: a number published, a string served.
            "amount_refunded": "42.00",
        }
    )


class DiscountQuote(BaseModel):
    """A discounted total. The bound on ``percent_off`` is published, not kept."""

    order_id: str = Field(examples=["ord-4471"])
    percent_off: int = Field(examples=[15], ge=0, le=100)
    total: float = Field(examples=[35.7])


@router.get(
    "/preman-probe/discount",
    response_model=DiscountQuote,
    responses={422: {"description": "A `percent_off` outside 0–100 is rejected."}},
    summary="An order total with a percentage discount applied",
    description=(
        "A fixture for PreMan's self-healing loop, and the only one here whose "
        "drift is on the way in. The published contract bounds `percent_off` to "
        "0–100 and documents HTTP 422 for anything else; the handler declares no "
        "bounds and answers 200 for any integer, including 150 and -40. The "
        "repair is to enforce the range the schema already documents."
    ),
)
def discount(
    percent_off: int = Query(
        default=15, description="Percentage off the order total. Documented as 0–100."
    ),
) -> JSONResponse:
    # The drift under test: no ge/le, so validation never runs and an
    # out-of-range percentage is accepted rather than rejected with a 422.
    return JSONResponse(
        {
            "order_id": "ord-4471",
            "percent_off": percent_off,
            "total": round(42.0 * (1 - percent_off / 100), 2),
        }
    )


class ShippingEstimate(BaseModel):
    """An honest contract, unlike ``OrderTotal`` above."""

    order_id: str = Field(examples=["ord-4471"])
    carrier: str = Field(examples=["Royal Mail"])
    business_days: int = Field(examples=[3])


@router.get(
    "/preman-probe/shipping-estimate",
    response_model=ShippingEstimate,
    summary="A delivery estimate for an order",
    description=(
        "A route with no history in PreMan's inventory. It exists to show that a "
        "push introducing an endpoint gets that endpoint tested on the same push, "
        "rather than only after the next repository scan."
    ),
)
def shipping_estimate() -> ShippingEstimate:
    return ShippingEstimate(order_id="ord-4471", carrier="Royal Mail", business_days=3)
