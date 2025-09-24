import type { SectionKey } from '../types/resume';

export const DEFAULT_SECTION_ORDER: SectionKey[] = [
  'personalInfo',
  'education',
  'projects',
  'workExperience',
  'skills',
  'honors',
  'summary'
];

export const normalizeSectionOrder = (order?: SectionKey[] | null): SectionKey[] => {
  const result: SectionKey[] = [];
  const source = Array.isArray(order) ? order : [];

  for (const key of source) {
    if (DEFAULT_SECTION_ORDER.includes(key) && !result.includes(key)) {
      result.push(key);
    }
  }

  for (const key of DEFAULT_SECTION_ORDER) {
    if (!result.includes(key)) {
      result.push(key);
    }
  }

  return result;
};
