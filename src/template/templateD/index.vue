<template>
  <div class="resume-container" :style="colorShadesStyle">
    <!-- 个人信息区域 -->
    <div class="header">
      <div class="header-main">
        <div class="personal-info">
          <h1 class="name">{{ resume.personalInfo.name }}</h1>
          <div class="info-row">
            <span>{{ resume.personalInfo.gender }}</span>
            <span>{{ resume.personalInfo.age }}岁</span>
            <span>{{ resume.personalInfo.university }}</span>
            <span>{{ resume.personalInfo.major }}</span>
          </div>
        </div>
        <div class="contact-info">
          <div class="contact-item">
            <span class="label">电话：</span>{{ resume.personalInfo.phone }}
          </div>
          <div class="contact-item">
            <span class="label">邮箱：</span>{{ resume.personalInfo.email }}
          </div>
          <div class="contact-item" v-if="resume.personalInfo.website">
            <span class="label">网站：</span>
            <a :href="resume.personalInfo.website" target="_blank">{{ resume.personalInfo.website }}</a>
          </div>
        </div>
      </div>
      <div class="avatar" v-if="resume.personalInfo.avatar">
        <img :src="resume.personalInfo.avatar" alt="头像">
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content">
      <!-- 个人总结 -->
      <section class="section" v-if="resume.summary">
        <h2 class="section-title">个人简介</h2>
        <div class="section-content summary" v-html="marked(resume.summary)"></div>
      </section>

      <!-- 教育经历 -->
      <section class="section" v-if="resume.education.length">
        <h2 class="section-title">教育经历</h2>
        <div class="section-content">
          <div class="edu-item" v-for="edu in resume.education" :key="edu.id">
            <div class="edu-header">
              <span class="school">{{ edu.school }}</span>
              <span class="time">{{ edu.startDate }} - {{ edu.endDate }}</span>
            </div>
            <div class="edu-info">{{ edu.major }} | {{ edu.degree }}</div>
          </div>
        </div>
      </section>

      <!-- 工作经历 -->
      <section class="section" v-if="resume.workExperience.length">
        <h2 class="section-title">工作经历</h2>
        <div class="section-content">
          <div class="work-item" v-for="work in resume.workExperience" :key="work.id">
            <div class="work-header">
              <div class="company">{{ work.company }}</div>
              <div class="time">{{ work.startDate }} - {{ work.endDate }}</div>
            </div>
            <div class="position">{{ work.position }}</div>
            <div class="description" v-html="marked(work.description)"></div>
          </div>
        </div>
      </section>

      <!-- 项目经验 -->
      <section class="section" v-if="resume.projects.length">
        <h2 class="section-title">项目经验</h2>
        <div class="section-content">
          <div class="project-item" v-for="project in resume.projects" :key="project.id">
            <div class="project-header">
              <div class="project-name">{{ project.projectName }}</div>
              <div class="time">{{ project.startDate }} - {{ project.endDate }}</div>
            </div>
            <div class="role">{{ project.role }}</div>
            <div class="brief" v-html="marked(project.briefIntroduction)"></div>
            <ul class="details">
              <li v-for="(desc, index) in String(project.description || '').split('\n')" :key="index"
                v-html="marked(desc)"></li>
            </ul>
          </div>
        </div>
      </section>

      <!-- 技能特长 -->
      <section class="section" v-if="resume.skills.length">
        <h2 class="section-title">技能特长</h2>
        <div class="section-content skills">
          <span class="skill-tag" v-for="skill in resume.skills" :key="skill.id"
            v-html="marked(skill.skillName)"></span>
        </div>
      </section>

      <!-- 荣誉奖项 -->
      <section class="section" v-if="resume.honors.length">
        <h2 class="section-title">荣誉奖项</h2>
        <div class="section-content">
          <div class="honor-item" v-for="honor in resume.honors" :key="honor.id">
            <span class="honor-name" v-html="marked(honor.honorName)"></span>
            <span class="honor-date">{{ honor.date }}</span>
          </div>
        </div>
      </section>
    </div>
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
  padding: 30px 40px;
  background: white;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 头部样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--color-lighter);
}

.header-main {
  flex: 1;
}

.name {
  font-size: 28px;
  color: var(--color-darker);
  margin: 0 0 12px;
}

.info-row {
  display: flex;
  gap: 20px;
  color: var(--color-dark);
  font-size: 14px;
}

.contact-info {
  margin-top: 15px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.contact-item {
  font-size: 14px;
}

.label {
  color: var(--color-base);
  margin-right: 5px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  margin-left: 20px;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 内容区域样式 */
.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  color: var(--color-darker);
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-lighter);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: var(--color-base);
}

/* 教育经历样式 */
.edu-item {
  margin-bottom: 15px;
}

.edu-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.school {
  font-weight: 500;
  color: var(--color-dark);
}

.time {
  color: var(--color-base);
  font-size: 14px;
}

/* 工作经历样式 */
.work-item {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px dashed var(--color-lighter);
}

.work-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.company {
  font-weight: 500;
  color: var(--color-dark);
}

.position {
  color: var(--color-base);
  margin-bottom: 8px;
}

.description {
  font-size: 14px;
  line-height: 1.6;
}

/* 项目经验样式 */
.project-item {
  margin-bottom: 25px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.project-name {
  font-weight: 500;
  color: var(--color-dark);
}

.role {
  color: var(--color-base);
  font-size: 14px;
  margin: 5px 0;
}

.brief {
  font-size: 14px;
  margin: 8px 0;
}

.details {
  list-style-type: circle;
  padding-left: 20px;
  margin: 10px 0;
  font-size: 14px;
  line-height: 1.6;
}

/* 技能标签样式 */
.skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.skill-tag {
  padding: 5px 12px;
  background: var(--color-lighter);
  border-radius: 15px;
  font-size: 13px;
  color: var(--color-dark);
}

/* 荣誉奖项样式 */
.honor-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-lighter);
}

.honor-name {
  color: var(--color-dark);
}

.honor-date {
  color: var(--color-base);
  font-size: 14px;
}

@media (max-width: 768px) {
  .resume-container {
    padding: 20px;
  }

  .header {
    flex-direction: column;
  }

  .avatar {
    margin: 20px auto 0;
  }

  .contact-info {
    grid-template-columns: 1fr;
  }
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>
