from app.config import Settings
from app.repositories.base import Repository
from app.repositories.dynamodb import DynamoDBRepository
from app.repositories.memory import MemoryRepository


def create_repository(settings: Settings) -> Repository:
    if settings.storage_backend == "dynamodb":
        return DynamoDBRepository(settings.table_name, settings.aws_region)
    return MemoryRepository()
