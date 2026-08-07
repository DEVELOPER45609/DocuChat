import shutil
import time
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile ,HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.users import User
from app.rag.ingestion import ingest_document, compute_file_hash
from app.schemas.document import DocumentRead, ChunkRead
from app.models.document import Document
from app.rag.vectorstore import delete_document_chunks, get_chunk_by_id



router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    temp_path = UPLOAD_DIR / f"{current_user.id}_{file.filename}"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Dedup check PEHLE karte hain — taake same file dobara embed na ho (expensive step)
    doc_id = compute_file_hash(temp_path)  
    existing = session.exec(
        select(Document).where(Document.doc_id == doc_id, Document.owner_id == current_user.id)
    ).first()

    if existing:
        temp_path.unlink(missing_ok=True)
        return existing

    try:
        _, chunk_count = ingest_document(
            file_path=temp_path,
            file_name=file.filename,
            user_id=current_user.id,
            upload_ts=time.time(),
        )
    except ValueError as e:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    document = Document(
        doc_id=doc_id,
        file_name=file.filename,
        chunk_count=chunk_count,
        owner_id=current_user.id,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    return document

@router.get("/", response_model=list[DocumentRead])
def list_documents(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    documents = session.exec(select(Document).where(Document.owner_id == current_user.id)).all()
    return documents

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    document = session.exec(
        select(Document).where(Document.doc_id == doc_id, Document.owner_id == current_user.id)
    ).first()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Vectorstore se chunks delete karo
    delete_document_chunks(current_user.id, doc_id)

    # Database se document record delete karo
    session.delete(document)
    session.commit()

    return {"detail": "Document deleted successfully"}


@router.get("/chunks/{chunk_id}", response_model=ChunkRead)
def get_chunk(
    chunk_id: str,
    current_user: User = Depends(get_current_user),
):
    chunk = get_chunk_by_id(current_user.id, chunk_id)

    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

    return ChunkRead(
        chunk_id=chunk["chunk_id"],
        text=chunk["text"],
        file_name=chunk["metadata"]["file_name"],
        page=chunk["metadata"]["page"],
    )