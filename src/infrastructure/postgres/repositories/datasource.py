from logging import Logger, getLogger
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func

from src.infrastructure.postgres.client import PostgresClient
from src.infrastructure.postgres.models import Datasource

from .base import BaseRepository


class DatasourceRepository(BaseRepository):
    def __init__(self, postgres_client: PostgresClient) -> None:
        self._logger: Logger = getLogger(__name__)
        super().__init__(postgres_client)

    async def create(self, name: str, description: str | None = None, embedding_model: str | None = None) -> Datasource:
        """Create a new datasource."""
        async with self._postgres_client.get_session() as session:
            datasource = Datasource(
                name=name,
                description=description,
                embedding_model=embedding_model
            )
            session.add(datasource)
            await session.commit()
            await session.refresh(datasource)
            self._logger.info(f"Created datasource: {datasource.id}")
            return datasource

    async def get_by_id(self, datasource_id: UUID) -> Optional[Datasource]:
        """Get a datasource by ID."""
        async with self._postgres_client.get_session() as session:
            stmt = select(Datasource).where(Datasource.id == datasource_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Datasource]:
        """Get all datasources with pagination."""
        async with self._postgres_client.get_session() as session:
            stmt = select(Datasource).order_by(Datasource.created_at.desc()).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_name(self, name: str) -> Optional[Datasource]:
        """Get a datasource by name."""
        async with self._postgres_client.get_session() as session:
            stmt = select(Datasource).where(Datasource.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update(self, datasource_id: UUID, **kwargs) -> Optional[Datasource]:
        """Update a datasource."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                update(Datasource)
                .where(Datasource.id == datasource_id)
                .values(**kwargs)
                .returning(Datasource)
            )
            result = await session.execute(stmt)
            await session.commit()
            updated_datasource = result.scalar_one_or_none()
            if updated_datasource:
                self._logger.info(f"Updated datasource: {datasource_id}")
            return updated_datasource

    async def delete(self, datasource_id: UUID) -> bool:
        """Delete a datasource and all its documents (cascade)."""
        async with self._postgres_client.get_session() as session:
            stmt = delete(Datasource).where(Datasource.id == datasource_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted = result.rowcount > 0
            if deleted:
                self._logger.info(f"Deleted datasource: {datasource_id}")
            return deleted

    async def count_all(self) -> int:
        """Count all datasources."""
        async with self._postgres_client.get_session() as session:
            stmt = select(func.count()).select_from(Datasource)
            result = await session.execute(stmt)
            count = result.scalar_one()
            return count
