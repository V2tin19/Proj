"""Resume export endpoints."""

import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import GeneratedResumeData
from app.services import usage_store
from app.services.docx_exporter import build_resume_docx

router = APIRouter()


@router.post("/export-resume/docx")
async def export_resume_docx(payload: GeneratedResumeData, request: Request):
    """Export generated resume data as a .docx Word document."""
    try:
        buf = await asyncio.get_running_loop().run_in_executor(
            None, build_resume_docx, payload
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成 Word 文件失败: {exc}") from exc

    actor = getattr(request.state, "user", None)
    usage_store.record_event(actor, "export_docx")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="resume.docx"'},
    )
