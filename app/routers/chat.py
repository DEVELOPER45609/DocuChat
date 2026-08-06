from fastapi import APIRouter,Depends
from app.core.deps import get_current_user
from app.models.users import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.rag.chain import ask_question
import json
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    def event_generator():
        for event in ask_question(
            user_id=current_user.id,
            question=request.question,
            doc_id=request.doc_id,
            chat_history=request.chat_history,
        ):
            yield f"data: {json.dumps(event)}\n\n"   #dict → JSON string → SSE format

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/compare")
def compare(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    def event_generator():
        for event in ask_question(
            user_id=current_user.id,
            question=request.question,
            doc_id=None,  # No specific document ID for comparison
            chat_history=request.chat_history,
        ):
            yield f"data: {json.dumps(event)}\n\n"   #dict → JSON string → SSE format

    return StreamingResponse(event_generator(), media_type="text/event-stream")