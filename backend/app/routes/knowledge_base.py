"""Knowledge base endpoints.

All blocking work (disk I/O, file parsing, embedding) runs in the default
executor so the event loop stays responsive for SSE streams.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    KnowledgeBaseConfig,
    KnowledgeBaseConfigUpdate,
    KnowledgeDocument,
    KnowledgeDocumentCreate,
)
from app.services import knowledge_base as kb_service
from app.services.document_parser import parse_file

router = APIRouter()

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = (".docx", ".pdf", ".txt", ".md")


@router.get("/knowledge-base/config", response_model=KnowledgeBaseConfig)
async def get_knowledge_base_config():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, kb_service.get_config)


@router.put("/knowledge-base/config", response_model=KnowledgeBaseConfig)
async def update_knowledge_base_config(payload: KnowledgeBaseConfigUpdate):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        kb_service.update_config,
        KnowledgeBaseConfig(**payload.model_dump()),
    )


@router.post("/knowledge-base/documents/upload", response_model=KnowledgeDocument, status_code=201)
async def upload_knowledge_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    lower_name = file.filename.lower()
    if not lower_name.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，仅支持 .docx / .pdf / .txt / .md",
        )

    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="文件大小超过 20MB 限制")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="文件大小超过 20MB 限制")

    def _parse_and_store() -> KnowledgeDocument:
        _, text = parse_file(file.filename, content)  # raises ValueError for bad files
        if not text.strip():
            raise ValueError("未能从文件中提取到文本内容")
        name = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
        return kb_service.add_document(name, "文件上传", text)

    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _parse_and_store)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {exc}") from exc


@router.get("/knowledge-base/documents", response_model=list[KnowledgeDocument])
async def get_knowledge_documents():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, kb_service.get_documents)


@router.post("/knowledge-base/documents", response_model=KnowledgeDocument, status_code=201)
async def create_knowledge_document(payload: KnowledgeDocumentCreate):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        kb_service.add_document,
        payload.name,
        payload.category,
        payload.content,
    )


@router.delete("/knowledge-base/documents/{document_id}")
async def delete_knowledge_document(document_id: str):
    loop = asyncio.get_running_loop()
    removed = await loop.run_in_executor(
        None,
        kb_service.remove_document,
        document_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"removed": True}
