import type { SectionKey } from '../types/resume';

/**
 * 简历分区的唯一术语来源:编辑器表单、预览模板、智能体页共用,
 * 禁止在别处硬编码分区标题文案。
 */
export const sectionLabels: Record<SectionKey, string> = {
  personalInfo: '个人信息',
  education: '教育经历',
  projects: '项目经历',
  workExperience: '工作经历',
  skills: '专业技能',
  honors: '荣誉奖项',
  summary: '自我评价'
};
