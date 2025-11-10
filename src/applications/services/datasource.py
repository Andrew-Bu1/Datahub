from logging import Logger, getLogger
from typing import List, Optional, Tuple
from uuid import UUID

from src.infrastructure.postgres.repositories import DatasourceRepository
from src.infrastructure.postgres.models import Datasource


class DatasourceService:
    def __init__(self, datasource_repository: DatasourceRepository) -> None:
        self.datasource_repository: DatasourceRepository = datasource_repository
        self._logger: Logger = getLogger(__name__)

    async def create_datasource(self, name: str, description: Optional[str] = None, embedding_model: str = "") -> Datasource:
        """Create a new datasource."""
        self._logger.info(f"Creating datasource: {name}")
        return await self.datasource_repository.create(name=name, description=description, embedding_model=embedding_model)
    
    async def get_datasource_by_id(self, datasource_id: UUID) -> Optional[Datasource]:
        """Get a datasource by ID."""
        return await self.datasource_repository.get_by_id(datasource_id)

    async def get_all_datasources(self, page: int = 1, page_size: int = 10) -> Tuple[List[Datasource], int]:
        """Get all datasources with pagination.
        
        Returns:
            Tuple of (datasources_list, total_count)
        """
        skip = (page - 1) * page_size
        datasources = await self.datasource_repository.get_all(skip=skip, limit=page_size)
        total = await self.datasource_repository.count_all()
        
        return datasources, total

    async def get_datasource_by_name(self, name: str) -> Optional[Datasource]:
        """Get a datasource by name."""
        return await self.datasource_repository.get_by_name(name)

    async def update_datasource(
        self, 
        datasource_id: UUID, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> Optional[Datasource]:
        """Update a datasource."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if embedding_model is not None:
            update_data["embedding_model"] = embedding_model
        
        if not update_data:
            # If no fields to update, just return the existing datasource
            return await self.datasource_repository.get_by_id(datasource_id)
        
        self._logger.info(f"Updating datasource: {datasource_id}")
        return await self.datasource_repository.update(datasource_id, **update_data)

    async def delete_datasource(self, datasource_id: UUID) -> bool:
        """Delete a datasource and all its documents."""
        self._logger.info(f"Deleting datasource: {datasource_id}")
        return await self.datasource_repository.delete(datasource_id)