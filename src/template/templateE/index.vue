<template>
  <div class="resume-container" :style="colorShadesStyle">
    <div class="header-decoration"></div>
    <!-- 头部信息区域 -->
    <header class="resume-header">
      <div class="header-content">
        <div class="header-main">
          <h1 class="name">{{ resume.personalInfo.name }}</h1>
          <div class="basic-info">
            <span v-if="resume.personalInfo.gender">{{ resume.personalInfo.gender }}</span>
            <span v-if="resume.personalInfo.age">{{ resume.personalInfo.age }}岁</span>
            <span v-if="resume.personalInfo.university">{{ resume.personalInfo.university }}</span>
            <span v-if="resume.personalInfo.major">{{ resume.personalInfo.major }}</span>
            <span v-if="resume.personalInfo.politicalStatus">{{ resume.personalInfo.politicalStatus }}</span>
          </div>
          <div class="contact-info">
            <a v-if="resume.personalInfo.phone" class="contact-item">
              <i class="fas fa-phone"></i>{{ resume.personalInfo.phone }}
            </a>
            <a v-if="resume.personalInfo.email" class="contact-item">
              <i class="fas fa-envelope"></i>{{ resume.personalInfo.email }}
            </a>
            <a v-if="resume.personalInfo.website" :href="resume.personalInfo.website" target="_blank"
              class="contact-item">
              <i class="fas fa-globe"></i>{{ resume.personalInfo.website }}
            </a>
          </div>
          <div v-if="resume.personalInfo.applicationPosition" class="job-target">
            意向职位: {{ resume.personalInfo.applicationPosition }}
          </div>
        </div>
        <div v-if="resume.personalInfo.avatar" class="avatar">
          <img :src="resume.personalInfo.avatar" alt="头像">
        </div>
      </div>
    </header>

    <!-- 个人总结 -->
    <section v-if="resume.summary" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-user"></i>
      </div>
      <h2 class="section-title">个人总结</h2>
      <div class="section-content summary" v-html="marked(resume.summary)"></div>
    </section>

    <!-- 教育经历 -->
    <section v-if="resume.education.length" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-graduation-cap"></i>
      </div>
      <h2 class="section-title">教育经历</h2>
      <div class="section-content">
        <div v-for="edu in resume.education" :key="edu.id" class="education-item">
          <div class="edu-main">
            <span class="school">{{ edu.school }}</span>
            <span v-if="edu.major" class="major">{{ edu.major }}</span>
            <span v-if="edu.degree" class="degree">{{ edu.degree }}</span>
          </div>
          <div class="edu-time">{{ edu.startDate }} ~ {{ edu.endDate }}</div>
        </div>
      </div>
    </section>

    <!-- 工作经历 -->
    <section v-if="resume.workExperience.length" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-briefcase"></i>
      </div>
      <h2 class="section-title">工作经历</h2>
      <div class="section-content">
        <div v-for="work in resume.workExperience" :key="work.id" class="work-item">
          <div class="work-header">
            <h3 class="company">{{ work.company }}</h3>
            <span class="time">{{ work.startDate }} ~ {{ work.endDate }}</span>
          </div>
          <div v-if="work.position" class="position">{{ work.position }}</div>
          <div v-if="work.description" class="description" v-html="marked(work.description)"></div>
        </div>
      </div>
    </section>

    <!-- 项目经历 -->
    <section v-if="resume.projects.length" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-project-diagram"></i>
      </div>
      <h2 class="section-title">项目经历</h2>
      <div class="section-content">
        <div v-for="project in resume.projects" :key="project.id" class="project-item">
          <div class="project-header">
            <h3 class="project-name">{{ project.projectName }}</h3>
            <span class="time">{{ project.startDate }} ~ {{ project.endDate }}</span>
          </div>
          <div v-if="project.role" class="role">{{ project.role }}</div>
          <div v-if="project.briefIntroduction" class="brief" v-html="marked(project.briefIntroduction)"></div>
          <ul v-if="project.description" class="description-list">
            <li v-for="(desc, index) in String(project.description).split('\n')" :key="index" v-html="marked(desc)">
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 技能特长 -->
    <section v-if="resume.skills.length" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-tools"></i>
      </div>
      <h2 class="section-title">技能特长</h2>
      <div class="section-content">
        <div class="skills-list">
          <span v-for="skill in resume.skills" :key="skill.id" class="skill-item"
            v-html="marked(skill.skillName)"></span>
        </div>
      </div>
    </section>

    <!-- 荣誉奖项 -->
    <section v-if="resume.honors.length" class="resume-section">
      <div class="section-icon">
        <i class="fas fa-award"></i>
      </div>
      <h2 class="section-title">荣誉奖项</h2>
      <div class="section-content">
        <div v-for="honor in resume.honors" :key="honor.id" class="honor-item">
          <span class="honor-name" v-html="marked(honor.honorName)"></span>
          <span class="honor-date">{{ honor.date }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useResumeStore } from '../../store/useResumeStore';
import { computed } from 'vue';
import type { ColorShades } from '../../types/color';
import { marked } from 'marked';
// 接受父组件的主题色
const props = defineProps<{
  colorShades: ColorShades;
}>();

// 动态生成 CSS 变量的样式
const colorShadesStyle = computed(() => ({
  '--color-lighter': props.colorShades.lighter,
  '--color-light': props.colorShades.light,
  '--color-base': props.colorShades.base,
  '--color-dark': props.colorShades.dark,
  '--color-darker': props.colorShades.darker,
}));

// 引入引用的store
const resumeStore = useResumeStore();

// 使用计算属性来获取store中的数据
const resume = computed(() => resumeStore.$state);
</script>

<style scoped>
.resume-container {
  max-width: 210mm;
  margin: 0 auto;
  padding: 20px;
  background: white;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.4;
  position: relative;
  overflow: hidden;
}

/* 头部装饰 */
.header-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 150px;
  height: 150px;
  background: var(--color-lighter);
  opacity: 0.1;
  border-radius: 0 0 0 100%;
  z-index: 0;
}

/* 头部样式优化 */
.resume-header {
  background: var(--color-base);
  margin: -20px -20px 25px;
  padding: 25px 20px 35px;
  color: white;
  position: relative;
  clip-path: polygon(0 0, 100% 0, 100% 85%, 0 95%);
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.header-main {
  flex: 1;
}

.name {
  font-size: 24px;
  margin: 0 0 6px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.basic-info {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  opacity: 0.9;
}

.contact-info {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}

.contact-item {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.job-target {
  font-size: 13px;
  opacity: 0.9;
}

/* 章节通用样式优化 */
.resume-section {
  margin-bottom: 20px;
  position: relative;
  padding-left: 25px;
}

.section-icon {
  position: absolute;
  left: 0;
  top: 3px;
  color: var(--color-base);
  width: 14px;
  text-align: center;
  font-size: 13px;
}

.section-title {
  font-size: 15px;
  color: var(--color-base);
  margin-bottom: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-lighter);
  margin-left: 8px;
}

/* 教育经历样式优化 */
.education-item {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.edu-main {
  display: flex;
  gap: 10px;
  align-items: center;
}

.school {
  font-size: 15px;
}

.major,
.degree {
  color: #666;
  font-size: 13px;
}

.edu-time {
  color: #666;
  font-size: 13px;
}

/* 工作经历样式优化 */
.work-item {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--color-lighter);
}

.work-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.company {
  font-size: 15px;
}

.position {
  color: var(--color-base);
  margin-bottom: 8px;
  font-size: 13px;
}

.description {
  color: #444;
  font-size: 13px;
}

/* 项目经历样式优化 */
.project-item {
  margin-bottom: 15px;
  padding: 12px;
  background: linear-gradient(to right, var(--color-lighter) 0%, transparent 1%);
  border-radius: 4px;
  border: none;
  transition: all 0.2s ease;
}

.project-item:hover {
  background: var(--color-lighter);
}

.project-header {
  margin-bottom: 6px;
}

.project-name {
  font-size: 15px;
}

.role,
.brief,
.description-list {
  font-size: 13px;
}

.role {
  color: var(--color-base);
  margin-bottom: 8px;
}

.brief {
  margin-bottom: 8px;
}

.description-list {
  margin: 6px 0;
  padding-left: 15px;
  list-style-type: circle;
}

.description-list li {
  margin-bottom: 3px;
  position: relative;
}

/* 技能标签样式优化 */
.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.skill-item {
  padding: 3px 10px;
  font-size: 12px;
  background: var(--color-lighter);
  border-radius: 20px;
  color: var(--color-dark);
  transition: all 0.2s ease;
}

.skill-item:hover {
  background: var(--color-light);
  transform: translateY(-1px);
}

/* 荣誉奖项样式优化 */
.honor-item {
  padding: 6px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed var(--color-lighter);
}

.honor-name {
  font-weight: 500;
}

.honor-date {
  color: #666;
}

/* 通用文本样式 */
.time,
.position,
.role,
.brief,
.description {
  font-size: 12px;
  color: #666;
}

.company,
.project-name,
.school {
  font-weight: 500;
  color: var(--color-dark);
}

/* 响应式优化 */
@media (max-width: 768px) {
  .resume-container {
    padding: 15px;
  }

  .resume-header {
    margin: -15px -15px 20px;
    padding: 20px 15px 25px;
  }

  .header-decoration {
    display: none;
  }

  .header-content {
    flex-direction: column-reverse;
    align-items: center;
    gap: 15px;
  }

  .avatar {
    width: 80px;
    height: 80px;
  }

  .header-main {
    text-align: center;
  }

  .basic-info,
  .contact-info {
    justify-content: center;
  }

  .education-item {
    flex-direction: column;
    gap: 5px;
  }

  .work-header {
    flex-direction: column;
    gap: 5px;
  }
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>
