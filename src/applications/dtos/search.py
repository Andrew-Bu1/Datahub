from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """Available search modes."""
    SEMANTIC = "semantic"  # Vector similarity search
    FULL_TEXT = "full_text"  # PostgreSQL full-text search
    HYBRID = "hybrid"  # Combination of semantic and full-text


class SimilarityMetric(str, Enum):
    """Distance metrics for vector similarity."""
    COSINE = "cosine"  # Cosine distance (1 - cosine similarity)
    L2 = "l2"  # Euclidean distance
    INNER_PRODUCT = "inner"  # Inner product (for normalized vectors)


class SearchRequest(BaseModel):
    datasource_id: UUID | list[UUID] = Field(..., description="Datasource ID(s) to search in")
    query: str = Field(..., description="User query text")
    search_mode: SearchMode = Field(
        default=SearchMode.SEMANTIC,
        description="Search mode: semantic, full_text, or hybrid"
    )
    similarity_metric: SimilarityMetric = Field(
        default=SimilarityMetric.COSINE,
        description="Distance metric for vector search: cosine, l2, or inner"
    )
    top_k: int = Field(default=5, ge=1, le=100, description="Number of top results to retrieve")


class SearchResult(BaseModel):
    chunk_id: UUID = Field(..., description="Unique identifier of the chunk")
    document_id: UUID = Field(..., description="Document ID containing this chunk")
    datasource_id: UUID = Field(..., description="Datasource ID")
    document_title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Chunk content text")
    chunk_index: int = Field(..., description="Index of chunk in document")
    score: float = Field(..., description="Relevance or similarity score (higher is better)")


class SearchResponse(BaseModel):
    datasource_ids: list[UUID] = Field(..., description="Datasource(s) searched")
    query: str = Field(..., description="User query text")
    search_mode: SearchMode = Field(..., description="Search mode used")
    similarity_metric: SimilarityMetric | None = Field(
        None, description="Distance metric used (for semantic/hybrid search)"
    )
    top_k: int = Field(..., description="Number of top results returned")
    results: list[SearchResult] = Field(..., description="List of retrieved top matching chunks")
