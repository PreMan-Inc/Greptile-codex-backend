from collections.abc import Collection

from app.config import Settings
from app.errors import AppError


def is_protected_demo_resource(
    settings: Settings,
    resource_id: str,
    protected_ids: Collection[str],
) -> bool:
    return settings.app_env == "demo" and resource_id in protected_ids


def require_mutable_demo_resource(
    settings: Settings,
    resource_id: str,
    protected_ids: Collection[str],
) -> None:
    if is_protected_demo_resource(settings, resource_id, protected_ids):
        raise AppError(
            403,
            "demo_resource_immutable",
            "Seeded demo resources are read-only",
        )
