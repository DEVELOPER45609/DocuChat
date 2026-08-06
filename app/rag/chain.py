from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.rag.llm import get_llm
from app.rag.vectorstore import get_vectorstore
from typing import Generator

SCORE_THRESHOLD = 0.3

CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Given the conversation history and a follow-up question, rewrite the
follow-up question as a standalone question that includes all necessary context.
If the follow-up question is already standalone, return it unchanged.
Only output the rewritten question, nothing else."""),
    ("human", "Chat History:\n{chat_history}\n\nFollow-up Question: {question}\n\nStandalone Question:"),
])


SYSTEM_PROMPT = """You are a document assistant. Answer ONLY using the context below.
If the context does not contain the answer, reply exactly:
"This information is not found in the uploaded documents."

Do not use any outside knowledge. Do not guess.

Context:
{context}
"""

COMPARE_SYSTEM_PROMPT = """You are a document assistant. Compare the provided documents and answer ONLY using the context below.
If the context does not contain the answer, reply exactly:
"This information is not found in the uploaded documents."

Do not use any outside knowledge. Do not guess.

Context:
{context}
"""

compare_prompt = ChatPromptTemplate.from_messages([
    ("system", COMPARE_SYSTEM_PROMPT),
    ("human", "{question}"),
    
])

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)

def retrieve_for_doc_ids(question: str, user_id: str, doc_ids: list[str]) -> list:
    vectorstore = get_vectorstore(user_id)
    search_kwargs = {"k": 6, "filter": {"doc_id": {"$in": doc_ids}}}
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(question, **search_kwargs)
    print(f"RETRIEVED: {len(docs_and_scores)} chunks")
    print("SCORES:", [round(s, 3) for _, s in docs_and_scores])
    filtered = [(doc, score) for doc, score in docs_and_scores if score >= SCORE_THRESHOLD]
    return [doc for doc, _ in filtered]

def format_compare_context(doc_id_to_chunks: dict[str, list]) -> str:
    """Har document ka apna labeled block banata hai, LLM ko clearly separate dikhane ke liye."""
    blocks = []
    for i, (doc_id, chunks) in enumerate(doc_id_to_chunks.items(), start=1):
        label = f"Document {i} (ID: {doc_id})"
        if chunks:
            file_name = chunks[0].metadata.get("file_name", "Unknown")
            body = format
            blocks.append(f"=== {label} — {file_name} ===\n{body}")
        else:
            blocks.append(f"=== {label} ===\nNo relevant information found in this document.")
    return "\n\n---\n\n".join(blocks)

def compare_documents(question: str, user_id: str, doc_ids: list[str]) -> Generator[dict, None, None]:
    all_chunks = []
    doc_id_to_chunks = {}
    for doc_id in doc_ids:
     
        chunks = retrieve_for_doc_ids(question, user_id, [doc_id])
        doc_id_to_chunks[doc_id] = chunks
        all_chunks.extend(chunks)
    if not all_chunks:
        yield {"type": "token", "content": "This information is not found in the uploaded documents."}
        yield {"type": "citations", "citations": []}
        return
    context = format_compare_context(doc_id_to_chunks)
    chain = compare_prompt | get_llm() | StrOutputParser()
    for token in chain.stream({"context": context, "question": question}):
        yield {"type": "token", "content": token}
    citations = build_citations(all_chunks)
    yield {"type": "citations", "citations": citations}

def format_chat_history(chat_history: list[dict]) -> str:
    if not chat_history:
        return "no previous conversation."
    lines = [f"{msg.role}: {msg.content}" for msg in chat_history]
    return "\n".join(lines)

def condense_question(question: str, chat_history: list[dict]) -> str:
    if not chat_history:
        return question
    formatted_history = format_chat_history(chat_history)
    chain = CONDENSE_PROMPT | get_llm() | StrOutputParser()
    standalone_question = chain.invoke({"chat_history": formatted_history, "question": question})
    return standalone_question

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
            "chunk_id": f"{c.metadata['doc_id']}:{c.metadata['page']}:{c.metadata['chunk_seq']}",
        }
        for c in chunks
    ]

def ask_question(question: str, user_id: str, doc_id: str | None = None, chat_history: list= None) -> Generator[dict, None, None]:
    standalone_question = condense_question(question, chat_history)
    vectorstore = get_vectorstore(user_id)
    search_kwargs = {"k": 6}
    if doc_id:
        search_kwargs["filter"] = {"doc_id": doc_id}
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(standalone_question, **search_kwargs)
    print(f"RETRIEVED: {len(docs_and_scores)} chunks")
    print("SCORES:", [round(s, 3) for _, s in docs_and_scores])
    filtered = [(doc, score) for doc, score in docs_and_scores if score >= SCORE_THRESHOLD]

    if not filtered:
        yield {"type": "token", "content": "This information is not found in the uploaded documents."}
            
        yield {"type": "citations", "citations": []}
        return
    
    chunks = [doc for doc, _ in filtered]
    context = format_context(chunks)

    chain = prompt | get_llm() | StrOutputParser()
    for token in chain.stream({"context": context, "question": standalone_question}):
        yield {"type": "token", "content": token}
    

    citations = build_citations(chunks)
    
    yield {"type": "citations", "citations": citations}
    












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


# User asks a question
#         │
#         ▼
# condense_question()
#         │
#         ▼
# Standalone question
#         │
#         ▼
# Vector Search (Chroma)
#         │
#         ▼
# Retrieved chunks + scores
#         │
#         ▼
# Apply SCORE_THRESHOLD
#         │
#         ▼
# Relevant chunks only
#         │
#         ▼
# Create context
#         │
#         ▼
# LLM generates answer
#         │
#         ▼
# invoke()  → one complete response
# or
# stream() → token-by-token using yield
#         │
#         ▼
# Return citation