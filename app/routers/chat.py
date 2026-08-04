from fastapi import APIRouter,Depends
from app.core.deps import get_current_user
from app.models.users import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.rag.chain import ask_question

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    result = ask_question(
        user_id=current_user.id,
        question=request.question,
        doc_id=request.doc_id,
    )
    return result