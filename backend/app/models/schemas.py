"""Pydantic models for request/response schemas."""

from __future__ import annotations

import re
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator


class PromptTemplate(BaseModel):
    id: str
    name: str
    style: str
    targetAudience: str
    description: str
    systemPrompt: str


class KnowledgeBaseConfig(BaseModel):
    chunkSize: int
    chunkOverlap: int
    retrievalTopK: int
    matchAlgorithm: str
    embeddingProvider: str


class KnowledgeBaseConfigUpdate(BaseModel):
    chunkSize: int = Field(..., ge=50, le=2000)
    chunkOverlap: int = Field(..., ge=0, le=500)
    retrievalTopK: int = Field(..., ge=1, le=100)
    matchAlgorithm: Literal["token-overlap", "vector-cosine"]
    embeddingProvider: Literal["local"]


class KnowledgeDocument(BaseModel):
    id: str
    name: str
    category: str
    content: str
    createdAt: str


class KnowledgeDocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="", max_length=100)
    content: str = Field(..., min_length=1, max_length=500_000)


class StudentEducationInput(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    startDate: str = ""
    endDate: str = ""


class StudentWorkInput(BaseModel):
    company: str = ""
    position: str = ""
    startDate: str = ""
    endDate: str = ""
    description: str = ""


class StudentProjectInput(BaseModel):
    projectName: str = ""
    role: str = ""
    startDate: str = ""
    endDate: str = ""
    briefIntroduction: str = ""
    description: str = ""


class ResumeGenerateRequest(BaseModel):
    name: str = ""
    gender: str = ""
    age: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    school: str = ""
    major: str = ""
    degree: str = ""
    politicalStatus: str = ""
    applicationPosition: str = ""
    targetRole: str = ""
    targetIndustry: str = ""
    ranking: str = ""
    courses: str = Field(default="", max_length=5_000)
    skillsText: str = Field(default="", max_length=5_000)
    honorsText: str = Field(default="", max_length=5_000)
    interests: str = Field(default="", max_length=2_000)
    selfIntroduction: str = Field(default="", max_length=10_000)
    templateId: str = ""
    enableRag: bool = True
    retrievalTopK: Optional[int] = Field(default=None, ge=1, le=100)
    wordCount: int = Field(default=800, ge=300, le=2000)
    educationExperiences: List[StudentEducationInput] = []
    workExperiences: List[StudentWorkInput] = []
    projectExperiences: List[StudentProjectInput] = []


def _none_to_empty(v: Any, info: ValidationInfo) -> Any:
    """LLM/前端数据里显式 null 一律按空串处理,避免校验 500。"""
    if v is None and info.field_name != "id":
        return ""
    return v


class PersonalInfo(BaseModel):
    name: str = ""
    gender: str = ""
    phone: str = ""
    email: str = ""
    university: str = ""
    politicalStatus: str = ""
    website: str = ""
    avatar: str = ""
    major: str = ""
    applicationPosition: str = ""
    age: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class EducationItem(BaseModel):
    id: int
    school: str = ""
    degree: str = ""
    major: str = ""
    startDate: str = ""
    endDate: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class WorkExperienceItem(BaseModel):
    id: int
    company: str = ""
    position: str = ""
    startDate: str = ""
    endDate: str = ""
    description: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class SkillItem(BaseModel):
    id: int
    skillName: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class ProjectItem(BaseModel):
    id: int
    projectName: str = ""
    role: str = ""
    startDate: str = ""
    endDate: str = ""
    briefIntroduction: str = ""
    description: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class HonorItem(BaseModel):
    id: int
    honorName: str = ""
    date: str = ""
    description: str = ""

    _coerce = field_validator("*", mode="before")(_none_to_empty)


class GeneratedResumeData(BaseModel):
    personalInfo: PersonalInfo
    education: List[EducationItem]
    workExperience: List[WorkExperienceItem]
    skills: List[SkillItem]
    projects: List[ProjectItem]
    honors: List[HonorItem]
    summary: str = ""


class KnowledgeHit(BaseModel):
    documentId: str
    documentName: str
    category: str
    score: float


class GeneratedResumeMeta(BaseModel):
    provider: Literal["llm", "local-fallback"]
    templateId: str
    templateName: str
    knowledgeHits: List[KnowledgeHit] = []
    fallbackReason: str = ""


class GeneratedResumeResponse(BaseModel):
    resumeData: GeneratedResumeData
    meta: GeneratedResumeMeta


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    stream: bool = Field(default=True, description="是否流式返回")


class HealthResponse(BaseModel):
    ok: bool
    now: str
    provider: str
    embedding: str = "unknown"
    auth: str = "disabled"


# ---------------------------------------------------------------------------
# 账号与鉴权(C/S 商业模式)
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(default="", max_length=254)
    inviteCode: str = Field(default="", max_length=64)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("密码须同时包含字母和数字")
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=32)
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token: str
    expiresAt: str
    username: str
    role: Literal["user", "admin"]


class AuthMeResponse(BaseModel):
    username: str
    role: Literal["user", "admin"]
    email: str = ""
