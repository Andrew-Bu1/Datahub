from abc import ABC, abstractmethod
from fastapi import APIRouter

class BaseController(ABC):  
    def __init__(self, *, prefix: str, tags: list[str]):
        self.router: APIRouter = APIRouter(prefix=prefix, tags=tags)

    @abstractmethod
    def register_routes(self) -> None:
        pass
