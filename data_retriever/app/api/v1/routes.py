from fastapi import APIRouter
from . import document
from . import datasource
from . import retrieval

router = APIRouter(prefix="/api/v1")

router.include_router(router=document.router, tags=["Documents"])
router.include_router(router=datasource.router, tags=["Datasource"])
router.include_router(router=retrieval.router, tags=["Retrieval"])