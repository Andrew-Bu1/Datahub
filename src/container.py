from functools import lru_cache

from src.applications.controllers import (
    DatasourceController,
    DocumentController,
    SearchController,
    BaseController
)
from src.applications.services import (
    DatasourceService,
    DocumentService,
    SearchService,
)
from src.configurations import Settings, get_settings
from src.infrastructure import AiHubClient, IdentityClient, PostgresClient
from src.infrastructure.postgres.repositories import DatasourceRepository, DocumentRepository, ChunkRepository


class Container:
    def __init__(self):
        self._settings: Settings = get_settings()

        # Core infrastructure
        self._postgres_client = PostgresClient(self._settings)
        self._aihub_client = AiHubClient(self._settings)
        # self._identity_client = IdentityClient(self._settings)

        # Lazy placeholders 
        self._repositories = {}
        self._services = {}
        self._controllers = {}

    # ------------------------------
    # Repositories
    # ------------------------------
    def _init_repositories(self):
        self._repositories = {
            "document": DocumentRepository(self._postgres_client),
            "datasource": DatasourceRepository(self._postgres_client),
            "chunk": ChunkRepository(self._postgres_client),
        }

    # ------------------------------
    # Services
    # ------------------------------
    def _init_services(self):
        self._services = {
            "document": DocumentService(
                self._repositories["document"],
                self._repositories["chunk"],
                self._aihub_client
            ),
            "datasource": DatasourceService(self._repositories["datasource"]),
            "search": SearchService(
                self._repositories["document"],
                self._aihub_client
            ),
        }

    # ------------------------------
    # Controllers
    # ------------------------------
    def _init_controllers(self) -> dict[str, BaseController]:
        self._controllers = {
            "document": DocumentController(self._services["document"]),
            "datasource": DatasourceController(self._services["datasource"]),
            "search": SearchController(self._services["search"]),
        }

    # ------------------------------
    # Public access
    # ------------------------------
    @property
    def controllers(self) -> list[any]:
        # Lazy initialization chain
        if not self._repositories:
            self._init_repositories()
        if not self._services:
            self._init_services()
        if not self._controllers:
            self._init_controllers()

        return list(self._controllers.values())

    @property
    def routers(self) -> list[any]:
        """Get all routers from controllers."""
        return [controller.router for controller in self.controllers]

    @property
    def postgres_client(self):
        return self._postgres_client

    async def startup(self):
        await self._postgres_client.initialize()

    async def shutdown(self):
        await self._postgres_client.dispose()


@lru_cache
def get_container() -> Container:
    return Container()
