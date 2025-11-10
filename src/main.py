from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.container import get_container, Container
from src.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: Container = get_container()
    await container.startup()

    yield

    await container.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(docs_url="/swagger", lifespan=lifespan)
    container: Container = get_container()
    setup_logging(container._settings.log_level)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    @app.get("/health")
    async def check_health():
        return {"health": "oke"}

    for router in container.routers:
        app.include_router(router)

    return app

app: FastAPI = create_app()
