from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.rag.llm import get_llm
from app.rag.vectorstore import get_vectorstore

SCORE_THRESHOLD = 0.3

SYSTEM_PROMPT = """You are a document assistant. Answer ONLY using the context below.
If the context does not contain the answer, reply exactly:
"This information is not found in the uploaded documents."

Do not use any outside knowledge. Do not guess.

Context:
{context}
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)

def format_context(chunks) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c.metadata['file_name']}, page {c.metadata['page']}]\n{c.page_content}")
    return "\n\n---\n\n".join(parts)


def build_citations(chunks) -> list[dict]:
    return [
        {
            "file_name": c.metadata["file_name"],
            "page": c.metadata["page"],
            "chunk_id": c.metadata["chunk_seq"],
        }
        for c in chunks
    ]


def ask_question(question: str, user_id: str, doc_id: str | None = None) -> dict:
    vectorstore = get_vectorstore(user_id)
    search_kwargs = {"k": 6}
    if doc_id:
        search_kwargs["filter"] = {"doc_id": doc_id}
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(question, **search_kwargs)
    print(f"RETRIEVED: {len(docs_and_scores)} chunks")
    print("SCORES:", [round(s, 3) for _, s in docs_and_scores])
    filtered = [(doc, score) for doc, score in docs_and_scores if score >= SCORE_THRESHOLD]

    if not filtered:
        return {
            "answer": "This information is not found in the uploaded documents.",
            "citations": [],
        }

    chunks = [doc for doc, _ in filtered]
    context = format_context(chunks)

    chain = prompt | get_llm() | StrOutputParser()
    response = chain.invoke({"context": context, "question": question})

    citations = build_citations(chunks)

    return {
        "answer": response,
        "citations": citations,
    }












# User Question
#       │
#       ▼
# Load user's vector store
#       │
#       ▼
# Search top 6 similar chunks
#       │
#       ▼
# Filter by SCORE_THRESHOLD
#       │
#       ├── No chunks → Return "Not found"
#       │
#       ▼
# Format retrieved chunks into context
#       │
#       ▼
# Send context + question to the LLM
#       │
#       ▼
# LLM generates an answer
#       │
#       ▼
# Create citations from chunk metadata
#       │
#       ▼
# Return:
# {
#   "answer": "...",
#   "citations": [...]
# }