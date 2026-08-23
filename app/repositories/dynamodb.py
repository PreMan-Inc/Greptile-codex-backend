from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, TypeVar

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from pydantic import BaseModel

from app.domain import (
    ProjectRecord,
    ProjectStatus,
    ResetTokenRecord,
    TaskRecord,
    TaskStatus,
    TokenRecord,
    UserRecord,
    json_payload,
)
from app.errors import DuplicateEntityError
from app.repositories.base import Repository

RecordT = TypeVar("RecordT", bound=BaseModel)


class DynamoDBRepository(Repository):
    """Single-table DynamoDB repository using only the table's `pk` key.

    Direct reads use typed keys, while user-scoped lists use scans. The latter is an
    intentional tradeoff for a small, dependency-free hackathon dataset and can be
    replaced by GSIs without changing the service layer.
    """

    def __init__(self, table_name: str, region_name: str) -> None:
        self._dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self._table = self._dynamodb.Table(table_name)

    def initialize(self) -> None:
        # The first strongly consistent seed read verifies table access. Avoid a
        # separate DescribeTable permission in the least-privilege Lambda role.
        return None

    @staticmethod
    def _item(pk: str, entity: str, record: BaseModel, **index: Any) -> dict[str, Any]:
        return {
            "pk": pk,
            "entity": entity,
            "payload": json.dumps(json_payload(record), separators=(",", ":")),
            **index,
        }

    @staticmethod
    def _parse(item: dict[str, Any] | None, model: type[RecordT]) -> RecordT | None:
        if not item:
            return None
        return model.model_validate_json(item["payload"])

    def _get(self, pk: str) -> dict[str, Any] | None:
        return self._table.get_item(Key={"pk": pk}, ConsistentRead=True).get("Item")

    def _put_unique(self, item: dict[str, Any]) -> None:
        try:
            self._table.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise DuplicateEntityError("entity already exists") from exc
            raise

    def _scan(self, expression: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        kwargs: dict[str, Any] = {"FilterExpression": expression}
        while True:
            response = self._table.scan(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key

    def create_user(self, user: UserRecord) -> UserRecord:
        email_key = f"EMAIL#{user.email.lower()}"
        # Reserve the email first. If the second write fails, release the reservation.
        self._put_unique({"pk": email_key, "entity": "email", "user_id": user.id})
        try:
            self._put_unique(
                self._item(
                    f"USER#{user.id}",
                    "user",
                    user,
                    email=user.email.lower(),
                )
            )
        except Exception:
            self._table.delete_item(Key={"pk": email_key})
            raise
        return user

    def get_user(self, user_id: str) -> UserRecord | None:
        return self._parse(self._get(f"USER#{user_id}"), UserRecord)

    def get_user_by_email(self, email: str) -> UserRecord | None:
        lookup = self._get(f"EMAIL#{email.lower()}")
        return self.get_user(str(lookup["user_id"])) if lookup else None

    def update_user(self, user: UserRecord) -> UserRecord:
        self._table.put_item(
            Item=self._item(
                f"USER#{user.id}",
                "user",
                user,
                email=user.email.lower(),
            )
        )
        return user

    def save_refresh_token(self, token: TokenRecord) -> None:
        self._table.put_item(
            Item=self._item(
                f"REFRESH#{token.token_hash}",
                "refresh_token",
                token,
                user_id=token.user_id,
                ttl=int(token.expires_at.timestamp()),
            )
        )

    def get_refresh_token(self, token_hash: str) -> TokenRecord | None:
        token = self._parse(self._get(f"REFRESH#{token_hash}"), TokenRecord)
        if not token or token.revoked or token.expires_at <= datetime.now(UTC):
            return None
        return token

    def revoke_refresh_token(self, token_hash: str) -> None:
        token = self.get_refresh_token(token_hash)
        if token:
            self.save_refresh_token(token.model_copy(update={"revoked": True}))

    def save_reset_token(self, token: ResetTokenRecord) -> None:
        self._table.put_item(
            Item=self._item(
                f"RESET#{token.token_hash}",
                "reset_token",
                token,
                user_id=token.user_id,
                ttl=int(token.expires_at.timestamp()),
            )
        )

    def consume_reset_token(self, token_hash: str) -> ResetTokenRecord | None:
        token = self._parse(self._get(f"RESET#{token_hash}"), ResetTokenRecord)
        if not token or token.consumed or token.expires_at <= datetime.now(UTC):
            return None
        consumed = token.model_copy(update={"consumed": True})
        self._table.put_item(Item=self._item(f"RESET#{token_hash}", "reset_token", consumed))
        return token

    def create_project(self, project: ProjectRecord) -> ProjectRecord:
        self._put_unique(
            self._item(
                f"PROJECT#{project.id}",
                "project",
                project,
                owner_id=project.owner_id,
                status=project.status.value,
            )
        )
        return project

    def get_project(self, owner_id: str, project_id: str) -> ProjectRecord | None:
        project = self._parse(self._get(f"PROJECT#{project_id}"), ProjectRecord)
        return project if project and project.owner_id == owner_id else None

    def list_projects(
        self, owner_id: str, status: ProjectStatus | None = None
    ) -> list[ProjectRecord]:
        expression = Attr("entity").eq("project") & Attr("owner_id").eq(owner_id)
        if status is not None:
            expression &= Attr("status").eq(status.value)
        projects = [
            project
            for item in self._scan(expression)
            if (project := self._parse(item, ProjectRecord)) is not None
        ]
        return sorted(projects, key=lambda item: (item.created_at, item.id), reverse=True)

    def update_project(self, project: ProjectRecord) -> ProjectRecord:
        self._table.put_item(
            Item=self._item(
                f"PROJECT#{project.id}",
                "project",
                project,
                owner_id=project.owner_id,
                status=project.status.value,
            )
        )
        return project

    def delete_project(self, owner_id: str, project_id: str) -> bool:
        project = self.get_project(owner_id, project_id)
        if not project:
            return False
        tasks = self.list_tasks(owner_id, project_id)
        with self._table.batch_writer() as batch:
            batch.delete_item(Key={"pk": f"PROJECT#{project_id}"})
            for task in tasks:
                batch.delete_item(Key={"pk": f"TASK#{task.id}"})
        return True

    def create_task(self, task: TaskRecord) -> TaskRecord:
        self._put_unique(
            self._item(
                f"TASK#{task.id}",
                "task",
                task,
                owner_id=task.owner_id,
                project_id=task.project_id,
                status=task.status.value,
            )
        )
        return task

    def get_task(self, owner_id: str, task_id: str) -> TaskRecord | None:
        task = self._parse(self._get(f"TASK#{task_id}"), TaskRecord)
        return task if task and task.owner_id == owner_id else None

    def list_tasks(
        self,
        owner_id: str,
        project_id: str,
        status: TaskStatus | None = None,
    ) -> list[TaskRecord]:
        expression = (
            Attr("entity").eq("task")
            & Attr("owner_id").eq(owner_id)
            & Attr("project_id").eq(project_id)
        )
        if status is not None:
            expression &= Attr("status").eq(status.value)
        tasks = [
            task
            for item in self._scan(expression)
            if (task := self._parse(item, TaskRecord)) is not None
        ]
        return sorted(tasks, key=lambda item: (item.created_at, item.id), reverse=True)

    def update_task(self, task: TaskRecord) -> TaskRecord:
        self._table.put_item(
            Item=self._item(
                f"TASK#{task.id}",
                "task",
                task,
                owner_id=task.owner_id,
                project_id=task.project_id,
                status=task.status.value,
            )
        )
        return task

    def delete_task(self, owner_id: str, task_id: str) -> bool:
        task = self.get_task(owner_id, task_id)
        if not task:
            return False
        self._table.delete_item(Key={"pk": f"TASK#{task_id}"})
        return True
