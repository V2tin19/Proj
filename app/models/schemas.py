"""Pydantic models for request/response schemas."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


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
    matchAlgorithm: str = Field(..., min_length=1, max_length=100)
    embeddingProvider: str = Field(..., min_length=1, max_length=100)


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


class EducationItem(BaseModel):
    id: int
    school: str = ""
    degree: str = ""
    major: str = ""
    startDate: str = ""
    endDate: str = ""


class WorkExperienceItem(BaseModel):
    id: int
    company: str = ""
    position: str = ""
    startDate: str = ""
    endDate: str = ""
    description: str = ""


class SkillItem(BaseModel):
    id: int
    skillName: str = ""


class ProjectItem(BaseModel):
    id: int
    projectName: str = ""
    role: str = ""
    startDate: str = ""
    endDate: str = ""
    briefIntroduction: str = ""
    description: str = ""


class HonorItem(BaseModel):
    id: int
    honorName: str = ""
    date: str = ""
    description: str = ""


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


class GeneratedResumeResponse(BaseModel):
    resumeData: GeneratedResumeData
    meta: dict


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    stream: bool = Field(default=True, description="是否流式返回")


class HealthResponse(BaseModel):
    ok: bool
    now: str
    provider: str
