from types import SimpleNamespace

from app.rag.chain import build_citations


def test_build_citations_includes_chunk_id():
    chunks = [
        SimpleNamespace(
            metadata={"file_name": "doc.txt", "page": 2, "chunk_seq": 7},
        ),
        SimpleNamespace(
            metadata={"file_name": "doc.txt", "page": 4, "chunk_seq": 9},
        ),
    ]

    citations = build_citations(chunks)

    assert citations == [
        {"file_name": "doc.txt", "page": 2, "chunk_id": 7},
        {"file_name": "doc.txt", "page": 4, "chunk_id": 9},
    ]
