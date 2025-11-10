from logging import Logger, getLogger
from typing import List, Optional, Any, Dict
from uuid import UUID

from sqlalchemy import select, update, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.postgres.client import PostgresClient
from src.infrastructure.postgres.models import Document

from .base import BaseRepository


class DocumentRepository(BaseRepository):
    def __init__(self, postgres_client: PostgresClient) -> None:
        super().__init__(postgres_client)
        self._logger: Logger = getLogger(__name__)

    async def create(
        self, 
        datasource_id: UUID, 
        title: str, 
        file_type: str,
        description: Optional[str] = None
    ) -> Document:
        """Create a new document."""
        async with self._postgres_client.get_session() as session:
            document = Document(
                datasource_id=datasource_id,
                title=title,
                file_type=file_type,
                description=description,
            )
            session.add(document)
            await session.commit()
            await session.refresh(document)
            self._logger.info(f"Created document: {document.id}")
            return document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        async with self._postgres_client.get_session() as session:
            stmt = select(Document).where(Document.id == document_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_datasource(
        self, 
        datasource_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """Get all documents for a datasource with pagination."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                select(Document)
                .where(Document.datasource_id == datasource_id)
                .order_by(Document.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, document_id: UUID, **kwargs) -> Optional[Document]:
        """Update a document."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(**kwargs)
                .returning(Document)
            )
            result = await session.execute(stmt)
            await session.commit()
            updated_document = result.scalar_one_or_none()
            if updated_document:
                self._logger.info(f"Updated document: {document_id}")
            return updated_document

    async def delete(self, document_id: UUID) -> bool:
        """Delete a document."""
        async with self._postgres_client.get_session() as session:
            stmt = delete(Document).where(Document.id == document_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted = result.rowcount > 0
            if deleted:
                self._logger.info(f"Deleted document: {document_id}")
            return deleted

    async def delete_by_datasource(self, datasource_id: UUID) -> int:
        """Delete all documents for a datasource. Returns number of deleted documents."""
        async with self._postgres_client.get_session() as session:
            stmt = delete(Document).where(Document.datasource_id == datasource_id)
            result = await session.execute(stmt)
            await session.commit()
            count = result.rowcount
            self._logger.info(f"Deleted {count} documents for datasource: {datasource_id}")
            return count

    async def count_by_datasource(self, datasource_id: UUID) -> int:
        """Count documents for a datasource."""
        async with self._postgres_client.get_session() as session:
            stmt = (
                select(func.count())
                .select_from(Document)
                .where(Document.datasource_id == datasource_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one()

    async def execute_raw_sql(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query and return results as list of dictionaries.
        
        Useful for complex queries like:
        - Full-text search using tsvector
        - Vector similarity search using pgvector
        - Hybrid search combining multiple techniques
        
        Args:
            query: Raw SQL query string (use :param_name for parameters)
            params: Dictionary of parameters to bind to query
            
        Returns:
            List of dictionaries, each representing a row
            
        Example:
            # Full-text search
            query = '''
                SELECT id, title, ts_rank(tcontent, query) as rank
                FROM chunks_384dimensions, plainto_tsquery('english', :search_text) query
                WHERE tcontent @@ query
                ORDER BY rank DESC
                LIMIT :limit
            '''
            results = await repo.execute_raw_sql(query, {'search_text': 'python', 'limit': 10})
            
            # Vector similarity search
            query = '''
                SELECT id, content, 1 - (embedding <=> :query_vector) as similarity
                FROM chunks_384dimensions
                WHERE datasource_id = :datasource_id
                ORDER BY embedding <=> :query_vector
                LIMIT :limit
            '''
            results = await repo.execute_raw_sql(query, {
                'query_vector': [0.1, 0.2, ...],
                'datasource_id': datasource_id,
                'limit': 10
            })
        """
        async with self._postgres_client.get_session() as session:
            stmt = text(query)
            result = await session.execute(stmt, params or {})
            
            # Convert rows to dictionaries
            rows = result.fetchall()
            if not rows:
                return []
            
            # Get column names from result
            columns = result.keys()
            
            # Convert each row to dictionary
            return [dict(zip(columns, row)) for row in rows]

    async def get_datasource_embedding_model(self, datasource_id: UUID) -> Optional[str]:
        """Get the embedding model for a datasource.
        
        This is a helper method to fetch the embedding_model from the datasource
        without needing a DatasourceRepository dependency.
        
        Args:
            datasource_id: The datasource UUID
            
        Returns:
            The embedding model name, or None if datasource not found
        """
        query = "SELECT embedding_model FROM datasources WHERE id = :datasource_id"
        result = await self.execute_raw_sql(query, {"datasource_id": str(datasource_id)})
        
        if result:
            return result[0].get("embedding_model")
        return None
