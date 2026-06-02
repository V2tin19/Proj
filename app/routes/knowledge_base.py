"""Knowledge base endpoints."""

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import KnowledgeBaseConfig, KnowledgeBaseConfigUpdate, KnowledgeDocument, KnowledgeDocumentCreate
from app.services import knowledge_base as kb_service
from app.services.document_parser import parse_file

router = APIRouter()


@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig)
async def get_knowledge_base_config():
    return kb_service.get_config()


@router.put("/knowledge-base/config", response_model=KnowledgeBaseConfig)
async def update_knowledge_base_config(payload: KnowledgeBaseConfigUpdate):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        kb_service.update_config,
        KnowledgeBaseConfig(**payload.model_dump()),
    )


@router.post("/knowledge-base/documents/upload", response_model=KnowledgeDocument, status_code=201)
async def upload_knowledge_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 20MB 限制")

    try:
        _, text = parse_file(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {exc}") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="未能从文件中提取到文本内容")

    # 使用文件名（去掉扩展名）作为文档名称
    name = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        kb_service.add_document,
        name,
        "文件上传",
        text,
    )


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
