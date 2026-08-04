from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    doc_id: str | None = None  # Optional document ID for context
    chat_history: list[ChatMessage] = []  # Optional chat history
    
class Citation(BaseModel):
    file_name: str
    page: int
    chunk_id: str
    
class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]    