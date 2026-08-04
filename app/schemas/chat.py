from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    doc_id: str | None = None  # Optional document ID for context
    
class Citation(BaseModel):
    file_name: str
    page: int
    chunk_id: int
    
class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]    