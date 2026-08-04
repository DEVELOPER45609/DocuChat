from langchain_chroma import Chroma
from app.core.config import settings
from app.rag.embeddings import get_embeddings

def get_vectorstore(user_id: str) -> Chroma:
    collection_name = f"user_{user_id}"
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )
    
 