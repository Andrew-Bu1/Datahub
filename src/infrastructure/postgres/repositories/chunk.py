"""Repository for chunk operations."""

from typing import List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.postgres.models import Chunks_384dimensions
from src.infrastructure.postgres.client import PostgresClient
from .base import BaseRepository


class ChunkRepository(BaseRepository):
    """Repository for managing document chunks with embeddings."""

    def __init__(self, postgres_client: PostgresClient):
        super().__init__(postgres_client)

    async def create_chunk(
        self,
        document_id: UUID,
        datasource_id: UUID,
        content: str,
        chunk_index: int,
        embedding: List[float],
    ) -> Chunks_384dimensions:
        """Create a new chunk with embedding."""
        async with self._postgres_client.get_session() as session:
            chunk = Chunks_384dimensions(
                document_id=document_id,
                datasource_id=datasource_id,
                content=content,
                chunk_index=chunk_index,
                embedding=embedding,
            )

            session.add(chunk)
            await session.commit()
            await session.refresh(chunk)

            return chunk

    async def create_chunks_bulk(
        self,
        chunks_data: List[dict],
    ) -> List[Chunks_384dimensions]:
        """Create multiple chunks in bulk for better performance."""
        async with self._postgres_client.get_session() as session:
            chunks = [
                Chunks_384dimensions(
                    document_id=chunk_data["document_id"],
                    datasource_id=chunk_data["datasource_id"],
                    content=chunk_data["content"],
                    chunk_index=chunk_data["chunk_index"],
                    embedding=chunk_data["embedding"],
                )
                for chunk_data in chunks_data
            ]

            session.add_all(chunks)
            await session.commit()

            # Refresh all chunks to get database-generated values
            for chunk in chunks:
                await session.refresh(chunk)

            return chunks

    async def get_by_document(
        self, document_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Chunks_384dimensions]:
        """Get all chunks for a document with pagination."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                select(Chunks_384dimensions)
                .where(Chunks_384dimensions.document_id == document_id)
                .order_by(Chunks_384dimensions.chunk_index)
                .offset(skip)
                .limit(limit)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_by_document(self, document_id: UUID) -> int:
        """Count total chunks for a document."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                select(func.count())
                .select_from(Chunks_384dimensions)
                .where(Chunks_384dimensions.document_id == document_id)
            )
            
            result = await session.execute(stmt)
            return result.scalar_one()

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document. Returns count of deleted chunks."""
        # Get count first
        count = await self.count_by_document(document_id)

        async with self._postgres_client.get_session() as session:
            # Delete all chunks
            stmt = select(Chunks_384dimensions).where(
                Chunks_384dimensions.document_id == document_id
            )
            result = await session.execute(stmt)
            chunks = result.scalars().all()

            for chunk in chunks:
                await session.delete(chunk)

            await session.commit()

        return count
