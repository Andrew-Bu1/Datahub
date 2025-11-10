from typing import List
from typing_extensions import override
from logging import Logger, getLogger

from src.applications.dtos.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchMode
)
from src.applications.services.search import SearchService

from .base import BaseController


class SearchController(BaseController):
    def __init__(self, search_service: SearchService) -> None:
        self._search_service: SearchService = search_service
        self._logger: Logger = getLogger(__name__)
        super().__init__(prefix="/search", tags=["Search"])
        self.register_routes()

    @override
    def register_routes(self):
        self.router.add_api_route(
            "", self.search, methods=["POST"], response_model=SearchResponse
        )

    async def search(self, payload: SearchRequest) -> SearchResponse:
        """Search for chunks across datasources.
        
        Supports three search modes:
        - semantic: Vector similarity search using embeddings
        - full_text: PostgreSQL full-text search
        - hybrid: Combination of semantic and full-text
        """
        # Normalize datasource_id to list
        datasource_ids = (
            [payload.datasource_id] 
            if not isinstance(payload.datasource_id, list) 
            else payload.datasource_id
        )
        
        self._logger.info(
            f"Search request: mode={payload.search_mode.value}, "
            f"query='{payload.query}', datasources={len(datasource_ids)}"
        )
        
        # Execute search
        results = await self._search_service.search(
            datasource_ids=datasource_ids,
            query=payload.query,
            search_mode=payload.search_mode,
            similarity_metric=payload.similarity_metric,
            top_k=payload.top_k
        )
        
        # Convert raw results to SearchResult DTOs
        search_results: List[SearchResult] = [
            SearchResult(
                chunk_id=result["chunk_id"],
                document_id=result["document_id"],
                datasource_id=result["datasource_id"],
                document_title=result["document_title"],
                content=result["content"],
                chunk_index=result["chunk_index"],
                score=float(result["score"])
            )
            for result in results
        ]
        
        return SearchResponse(
            datasource_ids=datasource_ids,
            query=payload.query,
            search_mode=payload.search_mode,
            similarity_metric=(
                payload.similarity_metric 
                if payload.search_mode in [SearchMode.SEMANTIC, SearchMode.HYBRID]
                else None
            ),
            top_k=payload.top_k,
            results=search_results
        )