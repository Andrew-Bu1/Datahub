from abc import ABC

from src.infrastructure.postgres.client import PostgresClient


class BaseRepository(ABC):
    """Base repository class for all repositories."""
    
    def __init__(self, postgres_client: PostgresClient) -> None:
        self._postgres_client: PostgresClient = postgres_client