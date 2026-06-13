"""Export GeneratedResumeData to a formatted .docx file."""

from __future__ import annotations

import io

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

from app.models.schemas import GeneratedResumeData

# 使用系统默认中文字体，避免字体缺失导致乱码
_BODY_FONT = "宋体"      # SimSun，几乎所有系统都有
_HEADING_FONT = "黑体"   # SimHei


def _set_run_font(run, size: int = 11, bold: bool = False, color: RGBColor | None = None, font_name: str = _BODY_FONT) -> None:
    font = run.font
    font.size = Pt(size)
    font.bold = bold
    font.name = font_name
    # 必须同时设置 eastAsia 字体，否则中文会显示为方框
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    if color:
        font.color.rgb = color


def _add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    size = 16 if level == 1 else 13
    _set_run_font(run, size=size, bold=True, color=RGBColor(0x1A, 0x23, 0x7E), font_name=_HEADING_FONT)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.space_before = Pt(12)


def _add_bullet_paragraph(doc: Document, text: str, indent_level: int = 0) -> None:
    p = doc.add_paragraph(style="List Bullet")
    run = p.runs[0] if p.runs else p.add_run(text)
    if not p.runs:
        p.add_run(text)
    else:
        p.runs[0].text = text
    for r in p.runs:
        _set_run_font(r, size=11)
    p.paragraph_format.left_indent = Inches(0.25 * (indent_level + 1))
    p.paragraph_format.space_after = Pt(3)


def _add_normal_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    _set_run_font(run, size=11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE


def build_resume_docx(data: GeneratedResumeData) -> io.BytesIO:
    """Build a Word document from generated resume data and return as BytesIO."""
    doc = Document()

    # Page margins
    sections = doc.sections[0]
    sections.top_margin = Inches(0.8)
    sections.bottom_margin = Inches(0.8)
    sections.left_margin = Inches(0.9)
    sections.right_margin = Inches(0.9)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("个人简历")
    _set_run_font(title_run, size=22, bold=True, color=RGBColor(0x1A, 0x23, 0x7E), font_name=_HEADING_FONT)
    title.paragraph_format.space_after = Pt(14)

    # Personal Info
    info = data.personalInfo
    info_parts = [
        f"姓名：{info.name}" if info.name else None,
        f"性别：{info.gender}" if info.gender else None,
        f"年龄：{info.age}" if info.age else None,
        f"电话：{info.phone}" if info.phone else None,
        f"邮箱：{info.email}" if info.email else None,
        f"学校：{info.university}" if info.university else None,
        f"专业：{info.major}" if info.major else None,
        f"应聘岗位：{info.applicationPosition}" if info.applicationPosition else None,
        f"个人主页：{info.website}" if info.website else None,
    ]
    info_line = "    ".join(p for p in info_parts if p)
    if info_line:
        p = doc.add_paragraph()
        run = p.add_run(info_line)
        _set_run_font(run, size=11)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)

    # Summary
    if data.summary:
        _add_heading(doc, "个人总结", level=2)
        _add_normal_paragraph(doc, data.summary)

    # Education
    if data.education:
        _add_heading(doc, "教育经历", level=2)
        for edu in data.education:
            date_range = f"{edu.startDate} - {edu.endDate}" if edu.startDate or edu.endDate else ""
            line = f"{edu.school}    {edu.degree}    {edu.major}    {date_range}".strip()
            if line:
                _add_bullet_paragraph(doc, line)

    # Work Experience
    if data.workExperience:
        _add_heading(doc, "实践 / 工作经历", level=2)
        for we in data.workExperience:
            header = f"{we.company}    {we.position}"
            date_range = f"{we.startDate} - {we.endDate}" if we.startDate or we.endDate else ""
            if date_range:
                header += f"    {date_range}"
            _add_bullet_paragraph(doc, header)
            if we.description:
                for desc_line in we.description.splitlines():
                    desc_line = desc_line.strip().lstrip("-").strip()
                    if desc_line:
                        _add_bullet_paragraph(doc, desc_line, indent_level=1)

    # Projects
    if data.projects:
        _add_heading(doc, "项目经历", level=2)
        for pr in data.projects:
            header = f"{pr.projectName}    {pr.role}"
            date_range = f"{pr.startDate} - {pr.endDate}" if pr.startDate or pr.endDate else ""
            if date_range:
                header += f"    {date_range}"
            _add_bullet_paragraph(doc, header)
            if pr.briefIntroduction:
                _add_bullet_paragraph(doc, pr.briefIntroduction, indent_level=1)
            if pr.description:
                for desc_line in pr.description.splitlines():
                    desc_line = desc_line.strip().lstrip("-").strip()
                    if desc_line:
                        _add_bullet_paragraph(doc, desc_line, indent_level=1)

    # Skills
    if data.skills:
        _add_heading(doc, "专业技能", level=2)
        skill_text = "、".join(s.skillName for s in data.skills if s.skillName)
        if skill_text:
            _add_normal_paragraph(doc, skill_text)

    # Honors
    if data.honors:
        _add_heading(doc, "荣誉奖项", level=2)
        for ho in data.honors:
            line = ho.honorName
            if ho.date:
                line += f"    {ho.date}"
            _add_bullet_paragraph(doc, line)
            if ho.description:
                _add_bullet_paragraph(doc, ho.description, indent_level=1)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
