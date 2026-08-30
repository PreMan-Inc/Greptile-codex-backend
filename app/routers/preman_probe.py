"""Fixtures for PreMan's own loops: one broken route, and three that work.

PreMan is meant to notice when an API stops behaving the way it publishes,
repair it, and open a pull request. Proving that end to end needs a real defect
on a real deployment, and inventing one by hand each time is slower than keeping
one here.

Exactly one route is *detectably* wrong at a time, and that is the point rather
than a tidy-up. A push where several watched endpoints fail at once cannot tell
you much: the run goes red either way, and every question worth asking
afterwards — did it find the right one, did it repair the right one, did the
pull request it opened address this failure or an older one — gets harder the
more failures there are to attribute it to. One failure against an otherwise
passing build is the case where the answer is unambiguous.

Which route carries the defect matters as much as the defect itself. Only three
of these are watched — ``order-total``, ``refund-status`` and ``discount`` — and
an unwatched endpoint is never called by an unattended run, so breaking
``shipping_estimate`` would produce a red route that no run ever looks at. That
reads exactly like PreMan failing to notice, which is the one outcome a fixture
must not be able to fake.

``refund_status`` is the one left wrong, and it fails by raising rather than by
answering wrongly. The handler reads ``refunded_at`` from a record that stores
the timestamp as ``settled_at``, so the lookup raises ``KeyError`` and the route
answers HTTP 500. That shape is deliberate: a 5xx is the least ambiguous
evidence there is that the code is at fault, which makes it the right defect to
prove the loop with before trying one that has to be argued about.

``refund_status`` also gains a documented ``currency`` field in this push, and
that is load-bearing rather than decorative. A push that changes no endpoint's
published contract is verified by a read-only campaign whose results arrive
after the run has already finished, so nothing it finds can reach the repair
step. Moving a contract is what makes the run take the path that can heal, which
means a fixture for the healing loop has to move one.

``order_total`` used to be the wrong one and now serves what it publishes. It
returns its model rather than a hand-built ``JSONResponse``, which is what makes
the repair real rather than cosmetic: FastAPI validates a returned model against
``response_model``, so the response can no longer drift from the schema
silently. Breaking it again means going back to a ``JSONResponse``, precisely
because that is what escapes the check — and that is the harder second case,
where the endpoint answers 200 and only the body is wrong.

``discount`` is wrong too, but it is *not* the failure under test, and the
distinction is worth keeping straight. Its drift is on the way in: the contract
bounds ``percent_off`` to 0–100 and documents a 422, and the handler enforces
neither, so ``percent_off=150`` is answered 200 with a negative total. The
watched contract, however, asserts only a 200 and the presence of ``order_id``,
``percent_off`` and ``total``, and it sends the default 15 — which satisfies all
four. So this route passes its own check while remaining wrong, which is why it
has never produced a repair. Catching it needs a case that sends an
out-of-range value, not a change to the handler.

``shipping_estimate`` serves a different purpose: an endpoint introduced by a
push, which is what proves the pre-push hook tests a route on the same push that
adds it rather than only after the next repository scan.

Read-only and no stored state, so the only thing they can break is a caller
expecting the published contract. To retire the fixture, delete this module and
its line in ``app.main``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["preman-probe"])


class OrderTotal(BaseModel):
    """What the endpoint promises, and what the handler now serves."""

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
        "A fixture for PreMan's self-healing loop. This one is honest: the "
        "handler returns its model, so FastAPI validates the response against "
        "the published schema and it cannot drift silently."
    ),
)
def order_total() -> OrderTotal:
    return OrderTotal(order_id="ord-4471", currency="GBP", total=42.0, paid=True)


class RefundStatus(BaseModel):
    """What a consumer reads before calling, and what the handler now ships."""

    order_id: str = Field(
        examples=["ord-4471"], description="Identifier of the refunded order."
    )
    state: str = Field(
        examples=["settled"],
        description="Where the refund has got to: `pending` or `settled`.",
    )
    amount_refunded: float = Field(
        examples=[42.0],
        description="Amount returned to the customer, in whole currency units.",
    )
    refunded_at: str = Field(
        examples=["2026-08-28T19:30:00Z"],
        description="When the refund settled, as an RFC 3339 timestamp in UTC.",
    )
    currency: str = Field(
        default="GBP",
        examples=["GBP"],
        description="ISO 4217 code that `amount_refunded` is denominated in.",
    )


# The settled refunds this fixture answers from. Stores the timestamp under
# `settled_at`, which is the name the ledger uses.
_REFUNDS = {
    "ord-4471": {
        "state": "settled",
        "amount": 42.0,
        "settled_at": "2026-08-28T19:30:00Z",
    },
}


@router.get(
    "/preman-probe/refund-status",
    response_model=RefundStatus,
    summary="A refund's state and the amount returned",
    description=(
        "A fixture for PreMan's self-healing loop. The handler reads "
        "`refunded_at` from a record that stores the timestamp as `settled_at`, "
        "so the route raises instead of answering. The repair is to read the "
        "field the record actually has."
    ),
)
def refund_status() -> RefundStatus:
    record = _REFUNDS["ord-4471"]
    return RefundStatus(
        order_id="ord-4471",
        state=record["state"],
        amount_refunded=record["amount"],
        # The defect under test: the record stores this as `settled_at`, so this
        # lookup raises KeyError and the endpoint answers HTTP 500.
        refunded_at=record["refunded_at"],
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
