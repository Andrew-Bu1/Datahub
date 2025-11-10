from typing_extensions import override
from uuid import UUID
from fastapi import Query, HTTPException, status, UploadFile, File, Form
import os
from logging import Logger, getLogger

from .base import BaseController

from src.applications.dtos.document import (
    # CreateDocumentRequest,
    DocumentResponse,
    ListDocumentResponse,
    UpdateDocumentRequest,
    PaginationParams,
)
from src.applications.services.document import DocumentService
from src.applications.services.chunking import ChunkerFactory


class DocumentController(BaseController):
    def __init__(self, document_service: DocumentService) -> None:
        self._document_service: DocumentService = document_service
        self._logger: Logger = getLogger(__name__)
        super().__init__(prefix="/datasources/{datasource_id}/documents", tags=["Documents"])
        self.register_routes()
    
    @override
    def register_routes(self):
        self.router.add_api_route(
            "", self.list_documents, methods=["GET"], response_model=ListDocumentResponse
        )
        self.router.add_api_route(
            "", self.create_document, methods=["POST"], response_model=DocumentResponse, status_code=201
        )
        self.router.add_api_route(
            "/{document_id}", self.get_document, methods=["GET"], response_model=DocumentResponse
        )
        self.router.add_api_route(
            "/{document_id}", self.update_document, methods=["PUT"], response_model=DocumentResponse
        )
        self.router.add_api_route(
            "/{document_id}",
            self.delete_document,
            methods=["DELETE"],
            status_code=204,
        )

    async def list_documents(
        self,
        datasource_id: UUID,
        page: int = Query(1, ge=1, description="Page Number"),
        page_size: int = Query(10, ge=1, le=100, description="Item per page"),
        search: str | None = Query(None, description="Search query"),
    ) -> ListDocumentResponse:
        """List all documents for a datasource with pagination."""
        documents, total = await self._document_service.get_documents_by_datasource(
            datasource_id=datasource_id,
            page=page,
            page_size=page_size
        )
        
        return ListDocumentResponse(
            data=[DocumentResponse.model_validate(doc) for doc in documents],
            pagination=PaginationParams(
                total=total,
                page=page,
                page_size=page_size
            )
        )

    async def create_document(
        self,
        datasource_id: UUID,
        # payload: CreateDocumentRequest,
        file: UploadFile = File(..., description="File to upload"),
    ) -> DocumentResponse:
        """Create a new document from uploaded file.
        
        The file will be uploaded and its metadata extracted:
        - title: Either provided or extracted from filename
        - file_type: Extracted from file extension
        """
        # Extract filename and extension
        filename = file.filename or "untitled"
        file_extension = os.path.splitext(filename)[1].lower().lstrip('.')
        
        # Determine file type from extension
        file_type_mapping = {
            'xlsx': 'excel',
            'xls': 'excel',
            'doc': 'word',
            'docx': 'word',
            'pdf': 'pdf',
            'txt': 'text',
            'csv': 'csv',
            'json': 'json',
            'xml': 'xml',
        }
        file_type = file_type_mapping.get(file_extension, file_extension)
        
        # Use provided title or extract from filename (without extension)
        document_title = filename
        
        # Create document in database
        document = await self._document_service.create_document(
            datasource_id=datasource_id,
            title=document_title,
            file_type=file_type,
        )
        
        try:
            # Read file content
            file_content = await file.read()
            self._logger.info(f"Processing file {filename} with type {file_type}")
            
            # Get appropriate chunker for file type
            chunker = ChunkerFactory.get_chunker(file_type)
            
            if chunker:
                # Process file and create chunks
                chunks = await chunker.process(file_content, filename)
                self._logger.info(f"Created {len(chunks)} chunks for document {document.id}")
                
                # Save chunks with embeddings to database
                try:
                    saved_chunks = await self._document_service.save_chunks_with_embeddings(
                        document_id=document.id,
                        datasource_id=datasource_id,
                        chunks=chunks
                    )
                    self._logger.info(
                        f"Successfully saved {len(saved_chunks)} chunks with embeddings "
                        f"for document {document.id}"
                    )
                except Exception as embed_error:
                    self._logger.error(
                        f"Error saving chunks with embeddings for document {document.id}: {embed_error}"
                    )
                    # Continue - document metadata is already saved
            else:
                self._logger.warning(
                    f"No chunker available for file type '{file_type}'. "
                    f"Supported types: {ChunkerFactory.get_supported_types()}"
                )
        except Exception as e:
            self._logger.error(f"Error processing file {filename}: {e}")
            # Don't fail the whole request, document metadata is already created
            # You might want to update document status to indicate processing failed
        
        return DocumentResponse.model_validate(document)

    async def get_document(
        self,
        datasource_id: UUID,
        document_id: UUID,
    ) -> DocumentResponse:
        """Get a document by ID."""
        document = await self._document_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found"
            )
        # Verify document belongs to the datasource
        if document.datasource_id != datasource_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found in datasource {datasource_id}"
            )
        return DocumentResponse.model_validate(document)

    async def update_document(
        self,
        datasource_id: UUID,
        document_id: UUID,
        payload: UpdateDocumentRequest,
    ) -> DocumentResponse:
        """Update a document."""
        # First check if document exists and belongs to the datasource
        existing_doc = await self._document_service.get_document_by_id(document_id)
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found"
            )
        if existing_doc.datasource_id != datasource_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found in datasource {datasource_id}"
            )
        
        document = await self._document_service.update_document(
            document_id=document_id,
            title=payload.title,
            description=payload.description
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found"
            )
        return DocumentResponse.model_validate(document)

    async def delete_document(
        self,
        datasource_id: UUID,
        document_id: UUID,
    ):
        """Delete a document."""
        # First check if document exists and belongs to the datasource
        existing_doc = await self._document_service.get_document_by_id(document_id)
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found"
            )
        if existing_doc.datasource_id != datasource_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found in datasource {datasource_id}"
            )
        
        deleted = await self._document_service.delete_document(document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} not found"
            )
        return None
