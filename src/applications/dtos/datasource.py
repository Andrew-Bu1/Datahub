from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CreateDatasourceRequest(BaseModel):
    name: str = Field(..., description="Name of the datasource")
    description: str | None = Field(..., description="Description of datasource")
    embedding_model: str = Field(..., description="embedding model for datasources")


class UpdateDatasourceRequest(BaseModel):
    name: str | None = Field(None, description="Name of the datasource")
    description: str | None = Field(None, description="Description of datasource")
    embedding_model: str | None = Field(None, description="embedding model for datasources")

class DatasourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    embedding_model: str
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")


class ListDatasourceResponse(BaseModel):
    data: list[DatasourceResponse] | None
    pagination: PaginationParams
