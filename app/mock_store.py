from __future__ import annotations

import copy
import json
import os
import tempfile
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Protocol

import boto3
from botocore.exceptions import ClientError

from app.config import Settings
from app.errors import AppError, DuplicateEntityError

RESOURCE_NAMES = ("customers", "products", "orders", "tickets", "reviews")
ID_PREFIXES = {
    "customers": "cus",
    "products": "prd",
    "orders": "ord",
    "tickets": "tkt",
    "reviews": "rev",
}
UNIQUE_FIELDS = {"customers": "email", "products": "sku"}
MAX_RECORDS_PER_RESOURCE = 250
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
SEED_PATH = Path(__file__).resolve().parent / "data" / "mock_db.json"


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _validate_document(document: dict[str, Any]) -> None:
    if not isinstance(document.get("meta"), dict):
        raise TypeError("Mock JSON document must contain a meta object")
    for resource in RESOURCE_NAMES:
        records = document.get(resource)
        if not isinstance(records, list):
            raise TypeError(f"Mock JSON document must contain a {resource} array")
        ids = [record.get("id") for record in records if isinstance(record, dict)]
        if len(ids) != len(records) or any(not item_id for item_id in ids):
            raise RuntimeError(f"Every {resource} record must contain an id")
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Mock JSON document contains duplicate {resource} ids")


class JsonDocumentBackend(Protocol):
    label: str

    def initialize(self) -> None: ...

    def read(self) -> dict[str, Any]: ...

    def write(self, document: dict[str, Any]) -> None: ...

    def reset(self) -> dict[str, Any]: ...


class ConcurrentWriteError(RuntimeError):
    """Raised when the JSON document changed during a read-modify-write cycle."""


class FileJsonBackend:
    """Atomic JSON-file storage for local development and tests."""

    label = "json-file"

    def __init__(self, data_path: Path, seed_path: Path = SEED_PATH) -> None:
        self.data_path = data_path
        self.seed_path = seed_path

    def initialize(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self.reset()
        _validate_document(self.read())

    def read(self) -> dict[str, Any]:
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def write(self, document: dict[str, Any]) -> None:
        _validate_document(document)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.data_path.parent,
                prefix=f".{self.data_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = temporary.name
            os.replace(temporary_path, self.data_path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def reset(self) -> dict[str, Any]:
        document = json.loads(self.seed_path.read_text(encoding="utf-8"))
        document["meta"]["updated_at"] = _now()
        self.write(document)
        return document


class S3JsonBackend:
    """Persistent hosted storage using one JSON document in a private S3 bucket."""

    label = "s3-json"

    def __init__(
        self,
        bucket: str,
        key: str,
        region_name: str,
        seed_path: Path = SEED_PATH,
    ) -> None:
        if not bucket:
            raise RuntimeError("MOCK_DATA_BUCKET is required for S3 mock storage")
        self.bucket = bucket
        self.key = key
        self.seed_path = seed_path
        self.client = boto3.client("s3", region_name=region_name)
        self._etag: str | None = None

    def initialize(self) -> None:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self.key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchKey", "NotFound"}:
                raise
            try:
                self._put(self._seed_document(), IfNoneMatch="*")
            except ClientError as create_exc:
                create_code = str(create_exc.response.get("Error", {}).get("Code", ""))
                if create_code not in {
                    "412",
                    "PreconditionFailed",
                    "ConditionalRequestConflict",
                }:
                    raise
        _validate_document(self.read())

    def read(self) -> dict[str, Any]:
        response = self.client.get_object(Bucket=self.bucket, Key=self.key)
        self._etag = response.get("ETag")
        return json.loads(response["Body"].read())

    def write(self, document: dict[str, Any]) -> None:
        conditions = {"IfMatch": self._etag} if self._etag else {"IfNoneMatch": "*"}
        try:
            self._put(document, **conditions)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"412", "PreconditionFailed", "ConditionalRequestConflict"}:
                raise ConcurrentWriteError("Mock JSON document changed concurrently") from exc
            raise

    def _put(self, document: dict[str, Any], **conditions: str) -> None:
        _validate_document(document)
        payload = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode()
        response = self.client.put_object(
            Bucket=self.bucket,
            Key=self.key,
            Body=payload,
            ContentType="application/json",
            ServerSideEncryption="AES256",
            **conditions,
        )
        self._etag = response.get("ETag")

    def reset(self) -> dict[str, Any]:
        document = self._seed_document()
        self._put(document)
        return document

    def _seed_document(self) -> dict[str, Any]:
        document = json.loads(self.seed_path.read_text(encoding="utf-8"))
        document["meta"]["updated_at"] = _now()
        return document


class JsonMockStore:
    """Thread-safe CRUD service whose source of truth is a single JSON document."""

    def __init__(self, backend: JsonDocumentBackend) -> None:
        self.backend = backend
        self._lock = RLock()
        self._initialized = False

    @property
    def storage_label(self) -> str:
        return self.backend.label

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self.backend.initialize()
            self._initialized = True

    def _read(self) -> dict[str, Any]:
        document = self.backend.read()
        _validate_document(document)
        return document

    def _write(self, document: dict[str, Any]) -> None:
        document["meta"]["updated_at"] = _now()
        document_bytes = len((json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode())
        if document_bytes > MAX_DOCUMENT_BYTES:
            raise AppError(
                409,
                "mock_data_limit_reached",
                "The shared mock JSON document has reached its size limit; reset or delete data",
                {"max_bytes": MAX_DOCUMENT_BYTES},
            )
        self.backend.write(document)

    def _mutate[ResultT](
        self,
        mutation: Callable[[dict[str, Any]], ResultT],
        *,
        attempts: int = 4,
    ) -> ResultT:
        for attempt in range(attempts):
            document = self._read()
            result = mutation(document)
            try:
                self._write(document)
            except ConcurrentWriteError as exc:
                if attempt + 1 == attempts:
                    raise AppError(
                        409,
                        "concurrent_write",
                        "The mock data changed concurrently; retry the request",
                    ) from exc
                continue
            return result
        raise AssertionError("unreachable")

    @staticmethod
    def _ensure_unique_in_document(
        document: dict[str, Any],
        resource: str,
        payload: dict[str, Any],
        *,
        excluding_id: str | None = None,
    ) -> None:
        field = UNIQUE_FIELDS.get(resource)
        if not field or field not in payload:
            return
        value = payload[field]
        normalized = value.casefold() if isinstance(value, str) else value
        for record in document[resource]:
            candidate = record.get(field)
            if isinstance(candidate, str):
                candidate = candidate.casefold()
            if candidate == normalized and record["id"] != excluding_id:
                singular = resource.removesuffix("s")
                raise AppError(
                    409,
                    f"duplicate_{singular}",
                    f"A {singular} with that {field} already exists",
                    {"field": field},
                )

    @staticmethod
    def _record_in_document(
        document: dict[str, Any], resource: str, item_id: str
    ) -> dict[str, Any] | None:
        return next(
            (record for record in document[resource] if record["id"] == item_id),
            None,
        )

    @classmethod
    def _require_reference_in_document(
        cls,
        document: dict[str, Any],
        resource: str,
        item_id: str,
        field: str,
    ) -> dict[str, Any]:
        record = cls._record_in_document(document, resource, item_id)
        if record is None:
            raise AppError(
                422,
                "invalid_reference",
                f"{field} does not reference an existing {resource.removesuffix('s')}",
                {"field": field, "value": item_id},
            )
        return record

    @classmethod
    def _prepare_in_document(
        cls,
        document: dict[str, Any],
        resource: str,
        payload: dict[str, Any],
        *,
        item_id: str | None = None,
        existing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prepared = copy.deepcopy(payload)
        merged = {**(existing or {}), **prepared}
        cls._ensure_unique_in_document(
            document,
            resource,
            merged,
            excluding_id=item_id,
        )

        if resource in {"orders", "tickets"}:
            cls._require_reference_in_document(
                document,
                "customers",
                merged["customer_id"],
                "customer_id",
            )
        elif resource == "reviews":
            cls._require_reference_in_document(
                document,
                "customers",
                merged["customer_id"],
                "customer_id",
            )
            cls._require_reference_in_document(
                document,
                "products",
                merged["product_id"],
                "product_id",
            )

        if resource == "orders":
            total_cents = 0
            for index, order_item in enumerate(merged["items"]):
                product = cls._record_in_document(
                    document,
                    "products",
                    order_item["product_id"],
                )
                if product is None:
                    raise AppError(
                        422,
                        "invalid_reference",
                        "Order item references an unknown product",
                        {
                            "field": f"items.{index}.product_id",
                            "value": order_item["product_id"],
                        },
                    )
                total_cents += product["price_cents"] * order_item["quantity"]
            prepared["total_cents"] = total_cents

        return prepared

    @staticmethod
    def _references_in_document(
        document: dict[str, Any], resource: str, item_id: str
    ) -> list[dict[str, str]]:
        references: list[dict[str, str]] = []
        if resource == "customers":
            for dependent in ("orders", "tickets", "reviews"):
                references.extend(
                    {"resource": dependent, "id": record["id"]}
                    for record in document[dependent]
                    if record.get("customer_id") == item_id
                )
        elif resource == "products":
            references.extend(
                {"resource": "orders", "id": record["id"]}
                for record in document["orders"]
                if any(order_item.get("product_id") == item_id for order_item in record["items"])
            )
            references.extend(
                {"resource": "reviews", "id": record["id"]}
                for record in document["reviews"]
                if record.get("product_id") == item_id
            )
        return references

    def reset(self) -> dict[str, int]:
        with self._lock:
            document = self.backend.reset()
            return {resource: len(document[resource]) for resource in RESOURCE_NAMES}

    def counts(self) -> dict[str, int]:
        with self._lock:
            document = self._read()
            return {resource: len(document[resource]) for resource in RESOURCE_NAMES}

    def list(
        self,
        resource: str,
        *,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        self._ensure_resource(resource)
        with self._lock:
            records = self._read()[resource]
            if q:
                needle = q.casefold()
                records = [
                    record
                    for record in records
                    if needle in json.dumps(record, ensure_ascii=False).casefold()
                ]
            total = len(records)
            return copy.deepcopy(records[offset : offset + limit]), total

    def get(self, resource: str, item_id: str) -> dict[str, Any] | None:
        self._ensure_resource(resource)
        with self._lock:
            for record in self._read()[resource]:
                if record["id"] == item_id:
                    return copy.deepcopy(record)
        return None

    def require(self, resource: str, item_id: str) -> dict[str, Any]:
        record = self.get(resource, item_id)
        if record is None:
            singular = resource.removesuffix("s")
            raise AppError(404, f"{singular}_not_found", f"{singular.title()} not found")
        return record

    def create(self, resource: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_resource(resource)
        with self._lock:
            now = _now()
            item_id = f"{ID_PREFIXES[resource]}_{uuid.uuid4().hex[:12]}"

            def add(document: dict[str, Any]) -> dict[str, Any]:
                if len(document[resource]) >= MAX_RECORDS_PER_RESOURCE:
                    raise AppError(
                        409,
                        "mock_data_limit_reached",
                        f"The shared {resource} collection has reached its record limit",
                        {"max_records": MAX_RECORDS_PER_RESOURCE},
                    )
                if any(item["id"] == item_id for item in document[resource]):
                    raise DuplicateEntityError(f"{resource.removesuffix('s')} already exists")
                prepared = self._prepare_in_document(document, resource, payload)
                record = {
                    "id": item_id,
                    **prepared,
                    "created_at": now,
                    "updated_at": now,
                }
                document[resource].append(copy.deepcopy(record))
                return record

            return copy.deepcopy(self._mutate(add))

    def replace(self, resource: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_resource(resource)
        with self._lock:

            def replace_record(document: dict[str, Any]) -> dict[str, Any]:
                for index, existing in enumerate(document[resource]):
                    if existing["id"] == item_id:
                        prepared = self._prepare_in_document(
                            document,
                            resource,
                            payload,
                            item_id=item_id,
                            existing=existing,
                        )
                        replacement = {
                            "id": item_id,
                            **prepared,
                            "created_at": existing["created_at"],
                            "updated_at": _now(),
                        }
                        document[resource][index] = replacement
                        return replacement
                singular = resource.removesuffix("s")
                raise AppError(404, f"{singular}_not_found", f"{singular.title()} not found")

            return copy.deepcopy(self._mutate(replace_record))

    def update(self, resource: str, item_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        self._ensure_resource(resource)
        with self._lock:

            def update_record(document: dict[str, Any]) -> dict[str, Any]:
                for index, existing in enumerate(document[resource]):
                    if existing["id"] == item_id:
                        prepared = self._prepare_in_document(
                            document,
                            resource,
                            changes,
                            item_id=item_id,
                            existing=existing,
                        )
                        updated = {**existing, **prepared, "updated_at": _now()}
                        document[resource][index] = updated
                        return updated
                singular = resource.removesuffix("s")
                raise AppError(404, f"{singular}_not_found", f"{singular.title()} not found")

            return copy.deepcopy(self._mutate(update_record))

    def delete(self, resource: str, item_id: str) -> bool:
        self._ensure_resource(resource)
        with self._lock:
            for attempt in range(4):
                document = self._read()
                references = self._references_in_document(document, resource, item_id)
                if references:
                    singular = resource.removesuffix("s")
                    raise AppError(
                        409,
                        f"{singular}_in_use",
                        f"Cannot delete {singular}; other mock records reference it",
                        {"references": references},
                    )
                remaining = [record for record in document[resource] if record["id"] != item_id]
                if len(remaining) == len(document[resource]):
                    return False
                document[resource] = remaining
                try:
                    self._write(document)
                except ConcurrentWriteError as exc:
                    if attempt == 3:
                        raise AppError(
                            409,
                            "concurrent_write",
                            "The mock data changed concurrently; retry the request",
                        ) from exc
                    continue
                return True
            raise AssertionError("unreachable")

    @staticmethod
    def _ensure_resource(resource: str) -> None:
        if resource not in RESOURCE_NAMES:
            raise ValueError(f"Unknown mock resource: {resource}")


def create_mock_store(settings: Settings) -> JsonMockStore:
    if settings.mock_storage_backend == "s3":
        backend: JsonDocumentBackend = S3JsonBackend(
            settings.mock_data_bucket,
            settings.mock_data_key,
            settings.aws_region,
        )
    else:
        backend = FileJsonBackend(Path(settings.mock_data_file))
    return JsonMockStore(backend)
