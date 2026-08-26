from __future__ import annotations

import json
from collections.abc import Callable
from io import BytesIO
from typing import Any

import pytest
from botocore.exceptions import ClientError

from app.errors import AppError
from app.mock_store import SEED_PATH, JsonMockStore, S3JsonBackend


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.etags: dict[tuple[str, str], str] = {}
        self.version = 0
        self.before_conditional_put: Callable[[FakeS3Client], None] | None = None
        self.before_create_put: Callable[[FakeS3Client], None] | None = None

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if (Bucket, Key) not in self.objects:
            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "HeadObject",
            )
        return {}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        object_key = (Bucket, Key)
        return {"Body": BytesIO(self.objects[object_key]), "ETag": self.etags[object_key]}

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        ServerSideEncryption: str,
        IfMatch: str | None = None,
        IfNoneMatch: str | None = None,
    ) -> dict[str, Any]:
        assert ContentType == "application/json"
        assert ServerSideEncryption == "AES256"
        object_key = (Bucket, Key)
        if IfNoneMatch == "*" and self.before_create_put is not None:
            callback = self.before_create_put
            self.before_create_put = None
            callback(self)
        if IfMatch is not None and self.before_conditional_put is not None:
            callback = self.before_conditional_put
            self.before_conditional_put = None
            callback(self)
        if IfMatch is not None and self.etags.get(object_key) != IfMatch:
            raise ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "ETag changed"}},
                "PutObject",
            )
        if IfNoneMatch == "*" and object_key in self.objects:
            raise ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "Object exists"}},
                "PutObject",
            )
        self.version += 1
        etag = f'"etag-{self.version}"'
        self.objects[object_key] = Body
        self.etags[object_key] = etag
        return {"ETag": etag}


def test_s3_json_backend_initializes_and_persists_across_store_instances(monkeypatch) -> None:
    fake_s3 = FakeS3Client()
    monkeypatch.setattr("app.mock_store.boto3.client", lambda *args, **kwargs: fake_s3)

    first_store = JsonMockStore(S3JsonBackend("mock-bucket", "mock_db.json", "us-east-1"))
    first_store.initialize()
    assert first_store.counts() == {
        "customers": 2,
        "products": 2,
        "orders": 2,
        "tickets": 2,
        "reviews": 2,
    }

    created = first_store.create(
        "customers",
        {
            "name": "Persistent Test Customer",
            "email": "persistent@example.com",
            "phone": "",
            "company": "Persistence Labs",
            "status": "active",
        },
    )

    second_store = JsonMockStore(S3JsonBackend("mock-bucket", "mock_db.json", "us-east-1"))
    second_store.initialize()
    assert second_store.get("customers", created["id"]) == created

    second_store.reset()
    assert second_store.get("customers", created["id"]) is None


def test_s3_retry_revalidates_and_recomputes_an_order_after_a_concurrent_write(
    monkeypatch,
) -> None:
    fake_s3 = FakeS3Client()
    monkeypatch.setattr("app.mock_store.boto3.client", lambda *args, **kwargs: fake_s3)
    store = JsonMockStore(S3JsonBackend("mock-bucket", "mock_db.json", "us-east-1"))
    store.initialize()

    def concurrent_order_change(client: FakeS3Client) -> None:
        object_key = ("mock-bucket", "mock_db.json")
        document = json.loads(client.objects[object_key])
        order = next(item for item in document["orders"] if item["id"] == "ord_seed_001")
        order["items"] = [{"product_id": "prd_seed_001", "quantity": 1}]
        order["total_cents"] = 7999
        client.version += 1
        client.objects[object_key] = json.dumps(document).encode()
        client.etags[object_key] = f'"etag-{client.version}"'

    fake_s3.before_conditional_put = concurrent_order_change
    updated = store.update("orders", "ord_seed_001", {"status": "shipped"})

    assert updated["status"] == "shipped"
    assert updated["items"] == [{"product_id": "prd_seed_001", "quantity": 1}]
    assert updated["total_cents"] == 7999


def test_store_rejects_growth_beyond_the_shared_collection_limit(monkeypatch) -> None:
    fake_s3 = FakeS3Client()
    monkeypatch.setattr("app.mock_store.boto3.client", lambda *args, **kwargs: fake_s3)
    monkeypatch.setattr("app.mock_store.MAX_RECORDS_PER_RESOURCE", 2)
    store = JsonMockStore(S3JsonBackend("mock-bucket", "mock_db.json", "us-east-1"))
    store.initialize()

    with pytest.raises(AppError) as raised:
        store.create(
            "customers",
            {
                "name": "Over Limit",
                "email": "over-limit@example.com",
                "phone": "",
                "company": "Limit Labs",
                "status": "active",
            },
        )

    assert raised.value.status_code == 409
    assert raised.value.code == "mock_data_limit_reached"


def test_s3_initialization_does_not_overwrite_a_competing_initializer(monkeypatch) -> None:
    fake_s3 = FakeS3Client()
    monkeypatch.setattr("app.mock_store.boto3.client", lambda *args, **kwargs: fake_s3)

    def competing_initialize(client: FakeS3Client) -> None:
        object_key = ("mock-bucket", "mock_db.json")
        document = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        document["customers"].append(
            {
                "id": "cus_competing_initializer",
                "name": "Competing Initializer",
                "email": "competing@example.com",
                "phone": "",
                "company": "Race Labs",
                "status": "active",
                "created_at": "2026-08-26T12:00:00Z",
                "updated_at": "2026-08-26T12:00:00Z",
            }
        )
        client.version += 1
        client.objects[object_key] = json.dumps(document).encode()
        client.etags[object_key] = f'"etag-{client.version}"'

    fake_s3.before_create_put = competing_initialize
    store = JsonMockStore(S3JsonBackend("mock-bucket", "mock_db.json", "us-east-1"))
    store.initialize()

    assert store.get("customers", "cus_competing_initializer") is not None
