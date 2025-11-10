from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CreateDocumentRequest(BaseModel):
    """DTO for creating a document - used with form data and file upload."""
    title: str | None = Field(None, description="Optional title (will be extracted from filename if not provided)")
    description: str | None = Field(None, description="Description of Document")


class UpdateDocumentRequest(BaseModel):
    title: str | None = Field(..., description="Name of the Document")
    description: str | None = Field(..., description="Description of Document")
    datasource_id: UUID = Field(..., description="id of datasource")


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    datasource_id: UUID
    title: str
    file_type: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")


class ListDocumentResponse(BaseModel):
    data: list[DocumentResponse] | None
    pagination: PaginationParams
