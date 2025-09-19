from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
class DataSource(BaseModel):
    id: UUID
    name: str
    type: str
    description: Optional[str] = None
    embedding_model_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True