<template>
  <div class="resume-container" :style="colorShadesStyle">
    <!-- 个人信息 -->
    <div class="personal-info">
      <div class="personal-details">
        <div class="detail-row">
          <span class="label">姓名：</span>
          <span class="value">{{ resume.personalInfo.name }}</span>
        </div>
        <div class="detail-row">
          <span class="label">性别：</span>
          <span class="value">{{ resume.personalInfo.gender }}</span>
        </div>
        <div class="detail-row">
          <span class="label">年龄：</span>
          <span class="value">{{ resume.personalInfo.age }}</span>
        </div>
        <div class="detail-row">
          <span class="label">电话：</span>
          <span class="value">{{ resume.personalInfo.phone }}</span>
        </div>
        <div class="detail-row">
          <span class="label">邮箱：</span>
          <span class="value">{{ resume.personalInfo.email }}</span>
        </div>
        <div class="detail-row">
          <span class="label">学校：</span>
          <span class="value">{{ resume.personalInfo.university }}</span>
        </div>
        <div class="detail-row">
          <span class="label">专业：</span>
          <span class="value">{{ resume.personalInfo.major }}</span>
        </div>
        <div class="detail-row">
          <span class="label">政治面貌：</span>
          <span class="value">{{ resume.personalInfo.politicalStatus }}</span>
        </div>
        <div class="detail-row">
          <span class="label">网站：</span>
          <a :href="resume.personalInfo.website" target="_blank" class="value">{{ resume.personalInfo.website }}</a>
        </div>
      </div>
      <div class="profile-image">
        <img :src="resume.personalInfo.avatar" alt="个人照片">
      </div>
    </div>

    <!-- 教育经历 -->
    <div class="section education-section" v-if="resume.education.length">
      <div class="section-title">教育经历</div>
      <div class="section-content">
        <div class="item" v-for="edu in resume.education" :key="edu.id">
          <span>{{ edu.school }} ({{ edu.degree }})</span>
          <strong v-if="edu.startDate && edu.endDate">{{ edu.startDate }} 至 {{ edu.endDate }}</strong>
        </div>
      </div>
    </div>

    <!-- 工作经历 -->
    <div class="section experience-section" v-if="resume.workExperience.length">
      <div class="section-title">工作经历</div>
      <div class="section-content">
        <div class="item" v-for="work in resume.workExperience" :key="work.id">
          <span>{{ work.company }} - {{ work.position }} ({{ work.startDate }} 至 {{ work.endDate }})</span>
          <p v-html="marked(work.description)"></p>
        </div>
      </div>
    </div>

    <!-- 技能 -->
    <div class="section skills-section" v-if="resume.skills.length">
      <div class="section-title">技能特长</div>
      <ul class="skills-list">
        <li v-for="skill in resume.skills" :key="skill.id" v-html="marked(skill.skillName)"></li>
      </ul>
    </div>

    <!-- 项目经验 -->
    <div class="section projects-section" v-if="resume.projects.length">
      <div class="section-title">项目经验</div>
      <div class="section-content">
        <div class="item" v-for="project in resume.projects" :key="project.id">
          <span>{{ project.projectName }} - {{ project.role }} ({{ project.startDate }} 至 {{ project.endDate }})</span>
          <p v-html="marked(project.briefIntroduction)"></p>
          <ul>
            <li v-for="(desc, index) in project.description.split('\n')" :key="index" v-html="marked(desc)"></li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 荣誉奖项 -->
    <div class="section honors-section" v-if="resume.honors.length">
      <div class="section-title">荣誉奖项</div>
      <div class="section-content">
        <div class="item" v-for="honor in resume.honors" :key="honor.id">
          <span>{{ honor.honorName }} ({{ honor.date }})</span>
          <p v-html="marked(honor.description)"></p>
        </div>
      </div>
    </div>

    <!-- 自我评价 -->
    <div class="section self-evaluation-section" v-if="resume.summary">
      <div class="section-title">自我评价</div>
      <p class="self-evaluation" v-html="marked(resume.summary)"></p>
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
/* 基本样式 */
body {
  background-color: #f5f5f5;
  margin: 0;
  font-size: 14px;
  font-family: Arial, sans-serif;
}

.resume-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.personal-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.personal-details {
  flex: 1;
}

.detail-row {
  display: flex;
  margin-bottom: 8px;
}

.label {
  font-weight: bold;
  margin-right: 8px;
}

.profile-image {
  text-align: center;
}

.profile-image img {
  width: 60px;
  height: auto;
  border-radius: 10px;
}

/* 各部分样式 */
.section-title {
  font-size: 18px;
  font-weight: bold;
  margin: 10px 0;
  padding: 5px;
  background-color: var(--color-lighter);
  border-left: 5px solid var(--color-base);
}

.section-content .item {
  margin-bottom: 5px;
}

.skills-list {
  list-style-type: disc;
  padding-left: 20px;
}

.self-evaluation {
  font-style: italic;
  margin-top: 10px;
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>
