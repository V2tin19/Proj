"""Knowledge base endpoints."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.models.schemas import KnowledgeBaseConfig, KnowledgeDocument, KnowledgeDocumentCreate
from app.services import knowledge_base as kb_service

router = APIRouter()


@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig)
async def get_knowledge_base_config():
    return kb_service.get_config()


@router.get("/knowledge-base/documents", response_model=list[KnowledgeDocument])
async def get_knowledge_documents():
    return kb_service.get_documents()


@router.post("/knowledge-base/documents", response_model=KnowledgeDocument, status_code=201)
async def create_knowledge_document(payload: KnowledgeDocumentCreate):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        kb_service.add_document,
        payload.name,
        payload.category,
        payload.content,
    )


@router.delete("/knowledge-base/documents/{document_id}")
async def delete_knowledge_document(document_id: str):
    loop = asyncio.get_event_loop()
    removed = await loop.run_in_executor(
        None,
        kb_service.remove_document,
        document_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"removed": True}
