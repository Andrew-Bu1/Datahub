from logging import Logger, getLogger
from typing import List, Optional, Tuple
from uuid import UUID

from src.infrastructure.postgres.repositories import DocumentRepository, ChunkRepository
from src.infrastructure.postgres.models import Document, Chunks_384dimensions
from src.infrastructure import AiHubClient
from src.applications.services.chunking import ChunkResult


class DocumentService:
    def __init__(
        self, 
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        aihub_client: AiHubClient
    ) -> None:
        self.document_repository: DocumentRepository = document_repository
        self.chunk_repository: ChunkRepository = chunk_repository
        self.aihub_client: AiHubClient = aihub_client
        self._logger: Logger = getLogger(__name__)

    async def create_document(
        self,
        datasource_id: UUID,
        title: str,
        file_type: str,
        description: Optional[str] = None
    ) -> Document:
        """Create a new document."""
        self._logger.info(f"Creating document: {title} for datasource: {datasource_id}")
        return await self.document_repository.create(
            datasource_id=datasource_id,
            title=title,
            file_type=file_type,
            description=description
        )

    async def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID."""
        return await self.document_repository.get_by_id(document_id)

    async def get_documents_by_datasource(
        self,
        datasource_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Document], int]:
        """Get all documents for a datasource with pagination.
        
        Returns:
            Tuple of (documents_list, total_count)
        """
        skip = (page - 1) * page_size
        documents = await self.document_repository.get_by_datasource(
            datasource_id, skip=skip, limit=page_size
        )
        
        # Get total count for this datasource
        total = await self.document_repository.count_by_datasource(datasource_id)
        
        return documents, total

    async def search_documents_by_title(
        self,
        title_query: str,
        limit: int = 50
    ) -> List[Document]:
        """Search documents by title."""
        # This method needs to be added to the repository
        # For now, returning empty list
        self._logger.info(f"Searching documents by title: {title_query}")
        return []

    async def update_document(
        self,
        document_id: UUID,
        title: Optional[str] = None,
        file_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Document]:
        """Update a document."""
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if file_type is not None:
            update_data["file_type"] = file_type
        if description is not None:
            update_data["description"] = description
        
        if not update_data:
            # If no fields to update, just return the existing document
            return await self.document_repository.get_by_id(document_id)
        
        self._logger.info(f"Updating document: {document_id}")
        return await self.document_repository.update(document_id, **update_data)

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document."""
        self._logger.info(f"Deleting document: {document_id}")
        return await self.document_repository.delete(document_id)

    async def save_chunks_with_embeddings(
        self,
        document_id: UUID,
        datasource_id: UUID,
        chunks: List[ChunkResult]
    ) -> List[Chunks_384dimensions]:
        """Save chunks with embeddings generated from AIHub.
        
        The embedding model is fetched from the datasource configuration.
        
        Args:
            document_id: The document ID
            datasource_id: The datasource ID
            chunks: List of ChunkResult objects from chunking service
            
        Returns:
            List of saved Chunks_384dimensions objects
        """
        if not chunks:
            self._logger.warning(f"No chunks to save for document {document_id}")
            return []
        
        # Fetch embedding model from datasource using raw SQL
        embedding_model = await self.document_repository.get_datasource_embedding_model(datasource_id)
        if not embedding_model:
            raise ValueError(f"Datasource {datasource_id} not found or has no embedding_model configured")
        
        self._logger.info(
            f"Generating embeddings for {len(chunks)} chunks using model: {embedding_model}"
        )
        
        try:
            # Prepare texts for embedding generation
            chunk_texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings via AIHub
            # The AIHub client returns: {"data": [{"embedding": [...], "index": 0}, ...]}
            embedding_response = await self.aihub_client.embedding(
                inputs=chunk_texts,
                model=embedding_model
            )
            
            # Extract embeddings from response
            embeddings_data = embedding_response.get("data", [])
            
            if len(embeddings_data) != len(chunks):
                raise ValueError(
                    f"Embedding count mismatch: got {len(embeddings_data)} embeddings "
                    f"for {len(chunks)} chunks"
                )
            
            # Sort by index to ensure correct ordering
            embeddings_data.sort(key=lambda x: x.get("index", 0))
            
            # Prepare chunks data for bulk insert
            chunks_data = []
            for chunk, embedding_item in zip(chunks, embeddings_data):
                embedding_vector = embedding_item.get("embedding", [])
                
                if len(embedding_vector) != 384:
                    self._logger.warning(
                        f"Unexpected embedding dimension: {len(embedding_vector)} "
                        f"(expected 384) for chunk {chunk.chunk_index}"
                    )
                
                chunks_data.append({
                    "document_id": document_id,
                    "datasource_id": datasource_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "embedding": embedding_vector,
                })
            
            # Bulk insert chunks
            saved_chunks = await self.chunk_repository.create_chunks_bulk(chunks_data)
            
            self._logger.info(
                f"Successfully saved {len(saved_chunks)} chunks with embeddings "
                f"for document {document_id}"
            )
            
            return saved_chunks
            
        except Exception as e:
            self._logger.error(
                f"Error saving chunks with embeddings for document {document_id}: {e}"
            )
            raise