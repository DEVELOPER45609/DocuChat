import tempfile
from pathlib import Path

from app.rag.ingestion import compute_file_hash, chunk_document
from langchain_core.documents import Document as LCDocument


def test_compute_file_hash_is_deterministic():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Hello DocuChat")
        temp_path = Path(f.name)

    hash1 = compute_file_hash(temp_path)
    hash2 = compute_file_hash(temp_path)

    assert hash1 == hash2  # same file → same hash, hamesha
    assert len(hash1) == 64  # sha256 hex digest length

    temp_path.unlink()


def test_compute_file_hash_differs_for_different_content():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f1:
        f1.write(b"Content A")
        path1 = Path(f1.name)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f2:
        f2.write(b"Content B")
        path2 = Path(f2.name)

    assert compute_file_hash(path1) != compute_file_hash(path2)

    path1.unlink()
    path2.unlink()


def test_chunk_document_adds_required_metadata():
    raw_docs = [LCDocument(page_content="A" * 2000, metadata={"page": 0})]

    chunks = chunk_document(raw_docs, doc_id="testhash123", file_name="test.txt", upload_ts=1234.5)

    assert len(chunks) > 1  # 2000 chars, chunk_size=800 → multiple chunks banne chahiye
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["doc_id"] == "testhash123"
        assert chunk.metadata["file_name"] == "test.txt"
        assert chunk.metadata["chunk_seq"] == i