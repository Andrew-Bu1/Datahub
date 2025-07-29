from fastapi import APIRouter

router = APIRouter(tags=["Documents"])

@router.get("/datasource/{datasource}/documents", summary="Get List of Documents")
async def get_documents(datasource: str):
    return {"message": f"Documents for datasource {datasource} endpoint is working!"}

@router.post("/datasource/{datasource}/documents", summary="Create a Document")
async def create_document(datasource: str):
    return {"message": f"Document created successfully in datasource {datasource}!"}

@router.put("/datasource/{datasource}/documents/{document_id}", summary="Update a Document")
async def update_document(datasource: str, document_id: str):
    return {"message": f"Document {document_id} in datasource {datasource} updated successfully!"}  

@router.delete("/datasource/{datasource}/documents/{document_id}", summary="Delete a Document")
async def delete_document(datasource: str, document_id: str):       
    return {"message": f"Document {document_id} in datasource {datasource} deleted successfully!"}  