<template>
  <div class="resume-container" :style="colorShadesStyle">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="profile-section">
        <div class="avatar-wrapper" v-if="resume.personalInfo.avatar">
          <img :src="resume.personalInfo.avatar" alt="头像" class="avatar">
        </div>
        <h1 class="name">{{ resume.personalInfo.name }}</h1>
        <p class="title">{{ resume.personalInfo.applicationPosition }}</p>
      </div>

      <div class="contact-section">
        <div class="contact-item" v-if="resume.personalInfo.phone">
          <i class="fas fa-phone"></i>
          <span>{{ resume.personalInfo.phone }}</span>
        </div>
        <div class="contact-item" v-if="resume.personalInfo.email">
          <i class="fas fa-envelope"></i>
          <span>{{ resume.personalInfo.email }}</span>
        </div>
        <div class="contact-item" v-if="resume.personalInfo.website">
          <i class="fas fa-globe"></i>
          <a :href="resume.personalInfo.website" target="_blank">个人网站</a>
        </div>
      </div>

      <div class="side-section">
        <h2 class="side-title">教育背景</h2>
        <div class="education-item" v-for="edu in resume.education" :key="edu.id">
          <h3>{{ edu.school }}</h3>
          <p class="edu-major">{{ edu.major }}</p>
          <p class="edu-degree">{{ edu.degree }}</p>
          <p class="edu-time">{{ edu.startDate }} - {{ edu.endDate }}</p>
        </div>
      </div>

      <div class="side-section">
        <h2 class="side-title">技能特长</h2>
        <div class="skills-wrapper">
          <span class="skill-tag" v-for="skill in resume.skills" :key="skill.id"
            v-html="marked(skill.skillName)"></span>
        </div>
      </div>
    </aside>

    <!-- 主要内容区域 -->
    <main class="main-content">
      <section class="content-section" v-if="resume.summary">
        <h2 class="section-title">个人简介</h2>
        <p class="summary" v-html="marked(resume.summary)"></p>
      </section>

      <section class="content-section" v-if="resume.workExperience.length">
        <h2 class="section-title">工作经历</h2>
        <div class="experience-item" v-for="work in resume.workExperience" :key="work.id">
          <div class="exp-header">
            <h3>{{ work.company }}</h3>
            <span class="exp-date">{{ work.startDate }} - {{ work.endDate }}</span>
          </div>
          <div class="exp-role">{{ work.position }}</div>
          <p class="exp-desc" v-html="marked(work.description)"></p>
        </div>
      </section>

      <section class="content-section" v-if="resume.projects.length">
        <h2 class="section-title">项目经验</h2>
        <div class="project-item" v-for="project in resume.projects" :key="project.id">
          <div class="proj-header">
            <h3>{{ project.projectName }}</h3>
            <span class="proj-date">{{ project.startDate }} - {{ project.endDate }}</span>
          </div>
          <div class="proj-role">{{ project.role }}</div>
          <p class="proj-brief" v-html="marked(project.briefIntroduction)"></p>
          <ul class="proj-details">
            <li v-for="(desc, index) in String(project.description || '').split('\n')" :key="index"
              v-html="marked(desc)"></li>
          </ul>
        </div>
      </section>

      <section class="content-section" v-if="resume.honors.length">
        <h2 class="section-title">荣誉奖项</h2>
        <div class="honors-list">
          <div class="honor-item" v-for="honor in resume.honors" :key="honor.id">
            <span class="honor-name" v-html="marked(honor.honorName)"></span>
            <span class="honor-date">{{ honor.date }}</span>
          </div>
        </div>
      </section>
    </main>
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
  display: grid;
  grid-template-columns: 300px 1fr;
  min-height: 297mm;
  width: 210mm;
  margin: 0 auto;
  background: white;
  box-shadow: 0 0 25px rgba(0, 0, 0, 0.05);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* 侧边栏样式 */
.sidebar {
  background: var(--color-darker);
  color: white;
  padding: 40px 30px;
}

.profile-section {
  text-align: center;
  margin-bottom: 30px;
}

.avatar-wrapper {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.2);
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px;
  color: white;
}

.title {
  font-size: 16px;
  color: var(--color-lighter);
  margin: 0;
}

.contact-section {
  margin-bottom: 30px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  color: var(--color-lighter);
}

.contact-item i {
  width: 16px;
  color: var(--color-light);
}

.contact-item a {
  color: var(--color-lighter);
  text-decoration: none;
}

.side-section {
  margin-bottom: 30px;
}

.side-title {
  font-size: 18px;
  color: white;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-light);
}

.education-item {
  margin-bottom: 20px;
}

.education-item h3 {
  font-size: 16px;
  margin: 0 0 5px;
  color: white;
}

.edu-major,
.edu-degree {
  color: var(--color-lighter);
  margin: 3px 0;
  font-size: 14px;
}

.edu-time {
  font-size: 12px;
  color: var(--color-light);
}

.skills-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  background: rgba(255, 255, 255, 0.1);
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 12px;
  color: var(--color-lighter);
}

/* 主要内容区域样式 */
.main-content {
  padding: 40px;
  background: white;
}

.content-section {
  margin-bottom: 35px;
}

.section-title {
  font-size: 20px;
  color: var(--color-darker);
  margin-bottom: 20px;
  position: relative;
  padding-bottom: 8px;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 30px;
  height: 3px;
  background: var(--color-base);
}

.summary {
  line-height: 1.6;
  color: #444;
}

.experience-item,
.project-item {
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.exp-header,
.proj-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.exp-header h3,
.proj-header h3 {
  font-size: 18px;
  color: var(--color-darker);
  margin: 0;
}

.exp-date,
.proj-date {
  font-size: 14px;
  color: #666;
}

.exp-role,
.proj-role {
  color: var(--color-base);
  font-size: 15px;
  margin-bottom: 8px;
}

.exp-desc,
.proj-brief {
  color: #444;
  line-height: 1.6;
  font-size: 14px;
}

.proj-details {
  list-style: none;
  padding-left: 0;
  margin: 10px 0 0;
}

.proj-details li {
  position: relative;
  padding-left: 15px;
  margin-bottom: 5px;
  font-size: 14px;
  line-height: 1.6;
  color: #444;
}

.proj-details li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-base);
}

.honors-list {
  display: grid;
  gap: 12px;
}

.honor-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.honor-name {
  color: #444;
  font-weight: 500;
}

.honor-date {
  color: #666;
  font-size: 14px;
}

@media print {
  .resume-container {
    box-shadow: none;
  }
}

@media (max-width: 768px) {
  .resume-container {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .sidebar {
    padding: 20px;
  }

  .main-content {
    padding: 20px;
  }
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>
