import hashlib
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.rag.vectorstore import get_vectorstore

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
}

def compute_file_hash(file_path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_document(file_path: Path):
    extension = file_path.suffix.lower()
    loader_class = LOADER_MAP.get(extension)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {extension}")
    loader = loader_class(file_path)
    return loader.load()

def chunk_document(raw_docs, doc_id: str, file_name: str, upload_ts: float):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
    )   
    chunks = text_splitter.split_documents(raw_docs)
    
    for seq, chunk in enumerate(chunks):
        page = chunk.metadata.get("page", 0)
        chunk.metadata.update({
            "doc_id": doc_id,
            "file_name": file_name,
            "upload_ts": upload_ts,
            "chunk_seq": seq,
            "page": page,
        })
    return chunks

def ingest_document(file_path: Path, file_name: str, user_id: int, upload_ts: float):
    doc_id = compute_file_hash(file_path)
    raw_docs = load_document(file_path)
    chunks = chunk_document(raw_docs, doc_id, file_name, upload_ts)
    vectorstore = get_vectorstore(user_id)
    ids = [f"{doc_id}:{c.metadata['page']}:{c.metadata['chunk_seq']}" for c in chunks]
    vectorstore.add_documents(chunks, ids=ids)

    return doc_id, len(chunks)