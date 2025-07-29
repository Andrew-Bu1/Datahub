from fastapi import FastAPI

from app.api.v1 import api_router

app = FastAPI(docs_url="/swagger", redoc_url="/redoc")

app.include_router(api_router)