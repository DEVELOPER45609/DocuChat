from types import SimpleNamespace
from app.rag.chain import build_citations


def test_build_citations_includes_chunk_id():
    chunks = [
        SimpleNamespace(
            metadata={"doc_id": "abc123", "file_name": "doc.txt", "page": 2, "chunk_seq": 7},
        ),
        SimpleNamespace(
            metadata={"doc_id": "abc123", "file_name": "doc.txt", "page": 4, "chunk_seq": 9},
        ),
    ]

    citations = build_citations(chunks)

    assert citations[0]["chunk_id"] == "abc123:2:7"
    assert citations[1]["chunk_id"] == "abc123:4:9"