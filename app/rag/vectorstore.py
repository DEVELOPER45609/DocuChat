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
    
def delete_document_chunks(user_id: int, doc_id: str):
    vectorstore = get_vectorstore(user_id)
    # Chroma se un sab chunks ko dhoondo jinka doc_id match kare, phir delete karo
    existing = vectorstore.get(where={"doc_id": doc_id})
    if existing and existing.get("ids"):
        vectorstore.delete(ids=existing["ids"])