"""FastAPI application entry point."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, HOST, PORT
from app.routes import chat, export, health, knowledge_base, resume, templates

app = FastAPI(
    title="AI Resume Backend",
    description="基于大模型的学生个人简历撰写智能体 —— Python FastAPI 后端",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run(app, host=HOST, port=PORT)
