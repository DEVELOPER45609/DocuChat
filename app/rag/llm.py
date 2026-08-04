from langchain_groq import ChatGroq
from app.core.config import settings

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=settings.GROQ_MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=0.7,
            
        )
    return _llm