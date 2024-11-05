from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class DocumentBase(BaseModel):
    name: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: str
    local_path: str
    status: str
    created_at: datetime
    updated_at: datetime
    original_filename: Optional[str] = None

    class Config:
        from_attributes = True