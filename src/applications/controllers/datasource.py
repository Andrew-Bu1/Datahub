from typing_extensions import override
from uuid import UUID
from fastapi import Query, HTTPException, status

from .base import BaseController

from src.applications.dtos.datasource import (
    CreateDatasourceRequest,
    DatasourceResponse,
    ListDatasourceResponse,
    UpdateDatasourceRequest,
    PaginationParams,
)
from src.applications.services.datasource import DatasourceService


class DatasourceController(BaseController):
    def __init__(self, datasource_service: DatasourceService) -> None:
        self._datasource_service: DatasourceService = datasource_service
        super().__init__(prefix="/datasources", tags=["Datasources"])
        self.register_routes()

    @override
    def register_routes(self):
        self.router.add_api_route(
            "", self.list_datasources, methods=["GET"], response_model=ListDatasourceResponse
        )
        self.router.add_api_route(
            "", self.create_datasource, methods=["POST"], response_model=DatasourceResponse, status_code=201
        )
        self.router.add_api_route(
            "/{datasource_id}", self.get_datasource, methods=["GET"], response_model=DatasourceResponse
        )
        self.router.add_api_route(
            "/{datasource_id}", self.update_datasource, methods=["PUT"], response_model=DatasourceResponse
        )
        self.router.add_api_route(
            "/{datasource_id}", self.delete_datasource, methods=["DELETE"], status_code=204
        )

    async def list_datasources(
        self,
        page: int = Query(1, ge=1, description="Page Number"),
        page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    ) -> ListDatasourceResponse:
        """List all datasources with pagination."""
        datasources, total = await self._datasource_service.get_all_datasources(
            page=page, page_size=page_size
        )
        
        return ListDatasourceResponse(
            data=[DatasourceResponse.model_validate(ds) for ds in datasources],
            pagination=PaginationParams(
                total=total,
                page=page,
                page_size=page_size
            )
        )

    async def create_datasource(self, payload: CreateDatasourceRequest) -> DatasourceResponse:
        """Create a new datasource."""
        datasource = await self._datasource_service.create_datasource(
            name=payload.name,
            description=payload.description,
            embedding_model=payload.embedding_model
        )
        return DatasourceResponse.model_validate(datasource)

    async def get_datasource(self, datasource_id: UUID) -> DatasourceResponse:
        """Get a datasource by ID."""
        datasource = await self._datasource_service.get_datasource_by_id(datasource_id)
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource with id {datasource_id} not found"
            )
        return DatasourceResponse.model_validate(datasource)

    async def update_datasource(
        self, 
        datasource_id: UUID, 
        payload: UpdateDatasourceRequest
    ) -> DatasourceResponse:
        """Update a datasource."""
        datasource = await self._datasource_service.update_datasource(
            datasource_id=datasource_id,
            name=payload.name,
            description=payload.description,
            embedding_model=payload.embedding_model
        )
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource with id {datasource_id} not found"
            )
        return DatasourceResponse.model_validate(datasource)

    async def delete_datasource(self, datasource_id: UUID):
        """Delete a datasource."""
        deleted = await self._datasource_service.delete_datasource(datasource_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource with id {datasource_id} not found"
            )
        return None

