from typing import Generic, TypeVar, List, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Base repository interface for CRUD operations.
    """

    @abstractmethod
    def create(self, item: T) -> T:
        """
        Create a new item in the repository.
        """
        pass

    @abstractmethod
    def read(self, item_id: int) -> Optional[T]:
        """
        Read an item from the repository by its ID.
        """
        pass

    @abstractmethod
    def update(self, item: T) -> T:
        """
        Update an existing item in the repository.
        """
        pass

    @abstractmethod
    def delete(self, item_id: int) -> None:
        """
        Delete an item from the repository by its ID.
        """
        pass

    @abstractmethod
    def list(self) -> List[T]:
        """
        List all items in the repository.
        """
        pass