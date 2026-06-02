"""Resume export endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import GeneratedResumeData
from app.services.docx_exporter import build_resume_docx

router = APIRouter()


@router.post("/export-resume/docx")
async def export_resume_docx(payload: GeneratedResumeData):
    """Export generated resume data as a .docx Word document."""
    try:
        buf = build_resume_docx(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成 Word 文件失败: {exc}") from exc

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="resume.docx"'},
    )
