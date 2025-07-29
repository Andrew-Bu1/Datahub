from fastapi import APIRouter

router = APIRouter(prefix="/datasources", tags=["Datasource"])

@router.get("", summary="Get List of Datasource")
async def get_datasource():
    return {"message": "Datasource endpoint is working!"}


@router.post("", summary="Create a Datasource")
async def create_datasource():
    return {"message": "Datasource created successfully!"}

@router.put("/{datasource_id}", summary="Update a Datasource")
async def update_datasource(datasource_id: str):
    return {"message": f"Datasource {datasource_id} updated successfully!"}

@router.delete("/{datasource_id}", summary="Delete a Datasource")
async def delete_datasource(datasource_id: str):
    return {"message": f"Datasource {datasource_id} deleted successfully!"}