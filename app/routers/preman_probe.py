"""One endpoint whose contract is deliberately wrong.

PreMan is meant to notice when an API stops matching the shape it publishes,
repair it, and open a pull request. Proving that end to end needs a real
mismatch on a real deployment, and inventing one by hand each time is slower
than keeping one here.

The drift is the ordinary kind: the schema promises ``total``, the handler
returns ``total_cents``. Same information, clearer name, and every consumer
reading ``total`` now gets nothing. Returning a ``JSONResponse`` is what makes
it observable — FastAPI validates a returned model against ``response_model``
and would otherwise correct the very thing being tested.

Read-only, no stored state, and it answers the same way every time, so the only
thing it can break is a caller expecting the published contract. To retire the
fixture, delete this module and its line in ``app.main``.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["preman-probe"])


class OrderTotal(BaseModel):
    """What the endpoint promises. The handler no longer honours ``total``."""

    order_id: str = Field(examples=["ord-4471"])
    currency: str = Field(examples=["GBP"])
    total: float = Field(examples=[42.0], description="Order total, in currency units.")


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
            # The drift under test: `total` renamed, the schema left behind.
            "total_cents": 4200,
        }
    )
