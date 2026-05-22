"""Resume generator — local fallback + LLM-powered generation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

from app.models.schemas import (
    EducationItem,
    GeneratedResumeData,
    GeneratedResumeResponse,
    HonorItem,
    PersonalInfo,
    ProjectItem,
    PromptTemplate,
    ResumeGenerateRequest,
    SkillItem,
    WorkExperienceItem,
)
from app.services.llm_client import call_openai_compatible


def _ensure_array(value: Any) -> list:
    return value if isinstance(value, list) else []


def _split_lines(text: str = "") -> List[str]:
    return [item.strip() for item in re.split(r"\r?\n|[;；]", str(text)) if item.strip()]


def _format_bullet_summary(lines: str, fallback: str) -> str:
    items = _split_lines(lines)
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


def _summarize_knowledge(references: List[dict]) -> str:
    if not references:
        return ""
    return "\n".join(
        f"{ref['documentName']}提示：{ref['content']}" for ref in references
    )


def _build_prompt_payload(input_data: ResumeGenerateRequest, template: PromptTemplate, references: List[dict]) -> dict:
    return {
        "template": template.model_dump(),
        "studentProfile": input_data.model_dump(),
        "knowledgeReferences": [
            {
                "documentName": ref["documentName"],
                "category": ref["category"],
                "excerpt": ref["content"],
            }
            for ref in references
        ],
    }


async def _call_llm(input_data: ResumeGenerateRequest, template: PromptTemplate, references: List[dict]) -> Dict[str, Any] | None:
    system_prompt = (
        f"{template.systemPrompt}\n"
        "你必须输出 JSON，字段结构为：personalInfo、education、workExperience、skills、projects、honors、summary。"
        "不要输出 markdown。"
    )
    user_prompt = json.dumps(_build_prompt_payload(input_data, template, references), ensure_ascii=False, indent=2)

    try:
        return await call_openai_compatible(system_prompt, user_prompt)
    except Exception as exc:
        logger.warning("LLM call failed, falling back to local generation: %s", exc)
        return None


def _generate_local(input_data: ResumeGenerateRequest, template: PromptTemplate, references: List[dict]) -> GeneratedResumeData:
    education_items = [
        EducationItem(
            id=index + 1,
            school=item.school or input_data.school or "",
            degree=item.degree or input_data.degree or "",
            major=item.major or input_data.major or "",
            startDate=item.startDate or "",
            endDate=item.endDate or "",
        )
        for index, item in enumerate(_ensure_array(input_data.educationExperiences))
    ]

    work_items = [
        WorkExperienceItem(
            id=100 + index,
            company=item.company or "",
            position=item.position or "",
            startDate=item.startDate or "",
            endDate=item.endDate or "",
            description=_format_bullet_summary(
                item.description,
                "负责相关工作内容，参与项目执行并完成阶段性成果。",
            ),
        )
        for index, item in enumerate(_ensure_array(input_data.workExperiences))
    ]

    project_items = [
        ProjectItem(
            id=200 + index,
            projectName=item.projectName or "",
            role=item.role or "项目成员",
            startDate=item.startDate or "",
            endDate=item.endDate or "",
            briefIntroduction=item.briefIntroduction or item.projectName or "",
            description=_format_bullet_summary(
                item.description,
                "围绕项目目标完成方案设计、实现与优化，并沉淀项目成果。",
            ),
        )
        for index, item in enumerate(_ensure_array(input_data.projectExperiences))
    ]

    skill_items = [
        SkillItem(id=300 + index, skillName=skill_name)
        for index, skill_name in enumerate(_split_lines(input_data.skillsText))
    ]

    honor_items = [
        HonorItem(
            id=400 + index,
            honorName=honor_name,
            date="",
            description="由智能体根据学生提供信息自动整理。",
        )
        for index, honor_name in enumerate(_split_lines(input_data.honorsText))
    ]

    course_text = "、".join(_split_lines(input_data.courses))
    ranking_text = f"成绩/排名：{input_data.ranking}" if input_data.ranking else ""
    interests_text = "、".join(_split_lines(input_data.interests))
    knowledge_summary = _summarize_knowledge(references)
    experience_count = len(project_items) + len(work_items)

    summary_parts = [
        f"{input_data.name or '该同学'}面向{input_data.targetRole or input_data.applicationPosition or '目标岗位'}进行求职，整体风格采用“{template.name}”。",
        input_data.selfIntroduction or "",
        f"课程基础涵盖：{course_text}。" if course_text else "",
        f"{ranking_text}。" if ranking_text else "",
        f"已沉淀{experience_count}段项目/实践经历，可支撑岗位匹配度表达。" if experience_count > 0 else "当前项目与实践经历较少，建议重点突出课程基础、获奖与综合素质。",
        f"兴趣方向：{interests_text}。" if interests_text else "",
        f"知识库参考：{knowledge_summary}" if knowledge_summary else "",
    ]

    summary = "\n".join(filter(None, summary_parts))

    return GeneratedResumeData(
        personalInfo=PersonalInfo(
            name=input_data.name or "",
            gender=input_data.gender or "",
            phone=input_data.phone or "",
            email=input_data.email or "",
            university=input_data.school or "",
            politicalStatus=input_data.politicalStatus or "",
            website=input_data.website or "",
            avatar="",
            major=input_data.major or "",
            applicationPosition=input_data.applicationPosition or input_data.targetRole or "",
            age=input_data.age or "",
        ),
        education=education_items or [EducationItem(
            id=1,
            school=input_data.school or "",
            degree=input_data.degree or "",
            major=input_data.major or "",
            startDate="",
            endDate="",
        )],
        workExperience=work_items,
        skills=skill_items,
        projects=project_items,
        honors=honor_items,
        summary=summary,
    )


def _normalize_llm_result(llm_result: dict) -> GeneratedResumeData:
    """Normalize LLM output to match our schema."""
    personal = llm_result.get("personalInfo", {}) if isinstance(llm_result.get("personalInfo"), dict) else {}
    return GeneratedResumeData(
        personalInfo=PersonalInfo(
            name=personal.get("name", ""),
            gender=personal.get("gender", ""),
            phone=personal.get("phone", ""),
            email=personal.get("email", ""),
            university=personal.get("university", personal.get("school", "")),
            politicalStatus=personal.get("politicalStatus", ""),
            website=personal.get("website", ""),
            avatar=personal.get("avatar", ""),
            major=personal.get("major", ""),
            applicationPosition=personal.get("applicationPosition", personal.get("targetRole", "")),
            age=str(personal.get("age") or ""),
        ),
        education=[
            EducationItem(
                id=edu.get("id", index + 1),
                school=edu.get("school", ""),
                degree=edu.get("degree", ""),
                major=edu.get("major", ""),
                startDate=edu.get("startDate", ""),
                endDate=edu.get("endDate", ""),
            )
            for index, edu in enumerate(llm_result.get("education") or [])
            if isinstance(edu, dict)
        ] or [EducationItem(id=1, school="", degree="", major="", startDate="", endDate="")],
        workExperience=[
            WorkExperienceItem(
                id=we.get("id", 100 + index),
                company=we.get("company", ""),
                position=we.get("position", we.get("title", "")),
                startDate=we.get("startDate", ""),
                endDate=we.get("endDate", ""),
                description=we.get("description", ""),
            )
            for index, we in enumerate(llm_result.get("workExperience") or [])
            if isinstance(we, dict)
        ],
        skills=[
            SkillItem(
                id=sk.get("id", 300 + index),
                skillName=sk.get("skillName", sk.get("name", ""))
            )
            for index, sk in enumerate(llm_result.get("skills") or [])
            if isinstance(sk, dict)
        ],
        projects=[
            ProjectItem(
                id=pr.get("id", 200 + index),
                projectName=pr.get("projectName", pr.get("name", "")),
                role=pr.get("role", ""),
                startDate=pr.get("startDate", ""),
                endDate=pr.get("endDate", ""),
                briefIntroduction=pr.get("briefIntroduction", ""),
                description=pr.get("description", ""),
            )
            for index, pr in enumerate(llm_result.get("projects") or [])
            if isinstance(pr, dict)
        ],
        honors=[
            HonorItem(
                id=ho.get("id", 400 + index),
                honorName=ho.get("honorName", ho.get("name", "")),
                date=ho.get("date", ""),
                description=ho.get("description", ""),
            )
            for index, ho in enumerate(llm_result.get("honors") or [])
            if isinstance(ho, dict)
        ],
        summary=llm_result.get("summary", "") if isinstance(llm_result.get("summary"), str) else "",
    )


async def generate_resume(
    input_data: ResumeGenerateRequest,
    template: PromptTemplate,
    references: List[dict],
) -> GeneratedResumeResponse:
    llm_result = await _call_llm(input_data, template, references)

    if llm_result:
        resume_data = _normalize_llm_result(llm_result)
        provider = "llm"
    else:
        resume_data = _generate_local(input_data, template, references)
        provider = "local-fallback"

    return GeneratedResumeResponse(
        resumeData=resume_data,
        meta={
            "provider": provider,
            "templateId": template.id,
            "templateName": template.name,
            "knowledgeHits": [
                {
                    "documentId": ref["documentId"],
                    "documentName": ref["documentName"],
                    "category": ref["category"],
                    "score": round(ref["score"], 4),
                }
                for ref in references
            ],
        },
    )
