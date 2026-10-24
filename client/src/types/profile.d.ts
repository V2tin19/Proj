import type { AgentConfig, ResumeSetting, SectionKey } from "./resume";
import type {
  Education, Honor, PersonalInfo, Project, Skill, WorkExperience
} from "./resume";

/** 一份简历档案的完整快照(不含 currentId/isFirstVisit 等运行态) */
export interface ProfileSnapshot {
  personalInfo: PersonalInfo;
  education: Education[];
  workExperience: WorkExperience[];
  skills: Skill[];
  projects: Project[];
  honors: Honor[];
  summary: string;
  sectionOrder: SectionKey[];
  resumeSetting: ResumeSetting;
  agentConfig: AgentConfig;
}

export interface ProfileMeta {
  id: string;
  name: string;
  remark: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProfileDetail extends ProfileMeta {
  data: ProfileSnapshot;
}
