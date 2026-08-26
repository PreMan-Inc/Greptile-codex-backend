from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Path, Query, Response, status
from pydantic import BaseModel

from app.dependencies import get_mock_store
from app.errors import AppError
from app.mock_schemas import (
    CustomerCreate,
    CustomerReplace,
    CustomerResponse,
    CustomerUpdate,
    MockPage,
    MockResetResponse,
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
from app.mock_store import JsonMockStore
from app.schemas import ErrorResponse

ERROR_DESCRIPTIONS = {
    404: "The requested mock record does not exist.",
    409: "The request conflicts with the current JSON document.",
    422: "The request body, query, or referenced record is invalid.",
}


def _error_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    return {
        status_code: {
            "model": ErrorResponse,
            "description": ERROR_DESCRIPTIONS[status_code],
        }
        for status_code in status_codes
    }


@dataclass(frozen=True)
class ResourceConfig:
    plural: str
    singular: str
    create_model: type[BaseModel]
    replace_model: type[BaseModel]
    update_model: type[BaseModel]
    response_model: type[BaseModel]

    @property
    def tag(self) -> str:
        return f"Mock {self.plural.title()}"


RESOURCE_CONFIGS = (
    ResourceConfig(
        "customers",
        "customer",
        CustomerCreate,
        CustomerReplace,
        CustomerUpdate,
        CustomerResponse,
    ),
    ResourceConfig(
        "products",
        "product",
        ProductCreate,
        ProductReplace,
        ProductUpdate,
        ProductResponse,
    ),
    ResourceConfig(
        "orders",
        "order",
        OrderCreate,
        OrderReplace,
        OrderUpdate,
        OrderResponse,
    ),
    ResourceConfig(
        "tickets",
        "ticket",
        TicketCreate,
        TicketReplace,
        TicketUpdate,
        TicketResponse,
    ),
    ResourceConfig(
        "reviews",
        "review",
        ReviewCreate,
        ReviewReplace,
        ReviewUpdate,
        ReviewResponse,
    ),
)

router = APIRouter(prefix="/mock")


def _model_payload(payload: BaseModel, *, partial: bool = False) -> dict[str, Any]:
    return payload.model_dump(mode="json", exclude_unset=partial)


def _build_resource_router(config: ResourceConfig) -> APIRouter:
    resource_router = APIRouter(prefix=f"/{config.plural}", tags=[config.tag])
    response_page = MockPage[config.response_model]

    def list_items(
        q: str | None = Query(
            default=None,
            min_length=1,
            max_length=100,
            description="Case-insensitive full-record search.",
        ),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        store: JsonMockStore = Depends(get_mock_store),
    ):
        items, total = store.list(config.plural, q=q, limit=limit, offset=offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    list_items.__name__ = f"mock_list_{config.plural}"
    resource_router.add_api_route(
        "",
        list_items,
        methods=["GET"],
        response_model=response_page,
        summary=f"List mock {config.plural}",
        description=(
            f"Return a paginated, searchable collection of JSON-backed mock {config.plural}."
        ),
        operation_id=f"mock_list_{config.plural}",
        responses=_error_responses(422),
    )

    def create_item(
        payload: Any,
        response: Response,
        store: JsonMockStore = Depends(get_mock_store),
    ):
        created = store.create(config.plural, _model_payload(payload))
        response.headers["Location"] = f"/api/v1/mock/{config.plural}/{created['id']}"
        return created

    create_item.__name__ = f"mock_create_{config.singular}"
    create_item.__annotations__["payload"] = config.create_model
    create_item.__annotations__["return"] = config.response_model
    resource_router.add_api_route(
        "",
        create_item,
        methods=["POST"],
        response_model=config.response_model,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create a mock {config.singular}",
        description=f"Validate and append one {config.singular} to the JSON document.",
        operation_id=f"mock_create_{config.singular}",
        responses=_error_responses(409, 422),
    )

    def get_item(
        item_id: str = Path(min_length=1, description=f"Mock {config.singular} identifier."),
        store: JsonMockStore = Depends(get_mock_store),
    ):
        return store.require(config.plural, item_id)

    get_item.__name__ = f"mock_get_{config.singular}"
    get_item.__annotations__["return"] = config.response_model
    resource_router.add_api_route(
        "/{item_id}",
        get_item,
        methods=["GET"],
        response_model=config.response_model,
        summary=f"Get a mock {config.singular}",
        description=f"Read one {config.singular} from the JSON document by its ID.",
        operation_id=f"mock_get_{config.singular}",
        responses=_error_responses(404, 422),
    )

    def replace_item(
        payload: Any,
        item_id: str = Path(min_length=1, description=f"Mock {config.singular} identifier."),
        store: JsonMockStore = Depends(get_mock_store),
    ):
        return store.replace(config.plural, item_id, _model_payload(payload))

    replace_item.__name__ = f"mock_replace_{config.singular}"
    replace_item.__annotations__["payload"] = config.replace_model
    replace_item.__annotations__["return"] = config.response_model
    resource_router.add_api_route(
        "/{item_id}",
        replace_item,
        methods=["PUT"],
        response_model=config.response_model,
        summary=f"Replace a mock {config.singular}",
        description=(
            f"Completely replace the writable fields of one JSON-backed {config.singular}."
        ),
        operation_id=f"mock_replace_{config.singular}",
        responses=_error_responses(404, 409, 422),
    )

    def update_item(
        payload: Any,
        item_id: str = Path(min_length=1, description=f"Mock {config.singular} identifier."),
        store: JsonMockStore = Depends(get_mock_store),
    ):
        return store.update(
            config.plural,
            item_id,
            _model_payload(payload, partial=True),
        )

    update_item.__name__ = f"mock_update_{config.singular}"
    update_item.__annotations__["payload"] = config.update_model
    update_item.__annotations__["return"] = config.response_model
    resource_router.add_api_route(
        "/{item_id}",
        update_item,
        methods=["PATCH"],
        response_model=config.response_model,
        summary=f"Update a mock {config.singular}",
        description=f"Partially update selected fields on one JSON-backed {config.singular}.",
        operation_id=f"mock_update_{config.singular}",
        responses=_error_responses(404, 409, 422),
    )

    def delete_item(
        item_id: str = Path(min_length=1, description=f"Mock {config.singular} identifier."),
        store: JsonMockStore = Depends(get_mock_store),
    ) -> Response:
        if not store.delete(config.plural, item_id):
            raise AppError(
                404,
                f"{config.singular}_not_found",
                f"{config.singular.title()} not found",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    delete_item.__name__ = f"mock_delete_{config.singular}"
    resource_router.add_api_route(
        "/{item_id}",
        delete_item,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        summary=f"Delete a mock {config.singular}",
        description=f"Remove one {config.singular} from the JSON document.",
        operation_id=f"mock_delete_{config.singular}",
        responses=_error_responses(404, 409, 422),
    )

    return resource_router


for resource_config in RESOURCE_CONFIGS:
    router.include_router(_build_resource_router(resource_config))


@router.post(
    "/reset",
    response_model=MockResetResponse,
    include_in_schema=False,
)
def reset_mock_data(store: JsonMockStore = Depends(get_mock_store)) -> MockResetResponse:
    counts = store.reset()
    return MockResetResponse(
        message="Mock data restored from app/data/mock_db.json",
        counts=counts,
        reset_at=datetime.now(UTC),
    )
