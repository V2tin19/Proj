"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # must run before app.config reads env vars

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware import AccessCodeMiddleware, RateLimitMiddleware
from app.routes import chat, export, health, knowledge_base, resume, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: data dir + SQLite schema + legacy migration + model warmup
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    import asyncio

    from app.services import embedding_service, kb_store
    from app.services.kb_store import init_db, migrate_from_json

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, init_db)
    await loop.run_in_executor(None, migrate_from_json)
    embedding_service.warmup_async()

    yield

    from app.services.llm_client import close_client

    await close_client()


app = FastAPI(
    title="AI Resume Backend",
    description="基于大模型的学生个人简历撰写智能体 —— Python FastAPI 后端",
    version="2.0.0",
    lifespan=lifespan,
)

# add_middleware: last added = outermost = runs first on the request path
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AccessCodeMiddleware)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])
app.include_router(knowledge_base.router, prefix="/api", tags=["Knowledge Base"])
app.include_router(resume.router, prefix="/api", tags=["Resume Generation"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(chat.router, prefix="/api", tags=["Chat Proxy"])


@app.get("/")
async def root():
    return {"message": "AI Resume Backend is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
