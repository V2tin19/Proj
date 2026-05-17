import type { Education, Honor, PersonalInfo, Project, Skill, WorkExperience } from "./resume";

export interface PromptTemplate {
  id: string;
  name: string;
  style: string;
  targetAudience: string;
  description: string;
  systemPrompt: string;
}

export interface KnowledgeBaseConfig {
  chunkSize: number;
  chunkOverlap: number;
  retrievalTopK: number;
  matchAlgorithm: string;
  embeddingProvider: string;
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  category: string;
  content: string;
  createdAt: string;
}

export interface StudentEducationInput {
  school: string;
  degree: string;
  major: string;
  startDate: string;
  endDate: string;
}

export interface StudentWorkInput {
  company: string;
  position: string;
  startDate: string;
  endDate: string;
  description: string;
}

export interface StudentProjectInput {
  projectName: string;
  role: string;
  startDate: string;
  endDate: string;
  briefIntroduction: string;
  description: string;
}

export interface ResumeGenerateRequest {
  name: string;
  gender: string;
  age: string;
  phone: string;
  email: string;
  website: string;
  school: string;
  major: string;
  degree: string;
  politicalStatus: string;
  applicationPosition: string;
  targetRole: string;
  targetIndustry: string;
  ranking: string;
  courses: string;
  skillsText: string;
  honorsText: string;
  interests: string;
  selfIntroduction: string;
  templateId: string;
  enableRag: boolean;
  retrievalTopK?: number;
  educationExperiences: StudentEducationInput[];
  workExperiences: StudentWorkInput[];
  projectExperiences: StudentProjectInput[];
}

export interface GeneratedResumeData {
  personalInfo: PersonalInfo;
  education: Education[];
  workExperience: WorkExperience[];
  skills: Skill[];
  projects: Project[];
  honors: Honor[];
  summary: string;
}

export interface GeneratedResumeResponse {
  resumeData: GeneratedResumeData;
  meta: {
    provider: string;
    templateId: string;
    templateName: string;
    knowledgeHits: Array<{
      documentId: string;
      documentName: string;
      category: string;
      score: number;
    }>;
  };
}
