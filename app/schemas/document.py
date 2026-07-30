from datetime import datetime
from pydantic import BaseModel

class DocumentRead(BaseModel):
    id: int
    doc_id: str
    file_name: str
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True