from fastapi import APIRouter

router = APIRouter(tags=["Retrieval"])

@router.post("/similarity", summary="Get Similarity Search Results")
async def similarity_search():
    return {"message": "Similarity search endpoint is working!"}    