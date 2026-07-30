from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    doc_id: str = Field(index=True)  # sha256 hash of file content
    file_name: str
    chunk_count: int
    owner_id: int = Field(foreign_key="user.id")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))