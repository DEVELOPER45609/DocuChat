from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.database import create_db_and_tables
from app.routers import auth, documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="DocuChat API",
    description="RAG Document Assistant with Grounded Citations",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/")
def health_check():
    return {"status": "ok", "app": "DocuChat"}