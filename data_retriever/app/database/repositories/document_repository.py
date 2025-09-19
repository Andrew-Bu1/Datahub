from app.database.repositories.base_repository import BaseRepository
from app.database.models.document import Document
from typing import List, Optional


class DocumentRepository(BaseRepository[Document]):
    async def create(self, item: Document) -> Document:
        # Implementation for creating a Document
        pass

    async def read(self, item_id: int) -> Optional[Document]:
        # Implementation for reading a Document by ID
        pass

    async def update(self, item: Document) -> Document:
        # Implementation for updating a Document
        pass

    async def delete(self, item_id: int) -> None:
        # Implementation for deleting a Document
        pass

    async def list(self) -> List[Document]:
        # Implementation for listing all Documents
        pass