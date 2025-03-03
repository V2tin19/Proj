<template>
  <div class="resume-container" :style="colorShadesStyle">
    <!-- 个人信息 -->
    <div class="personal-info">
      <div class="personal-details">
        <div class="contact-details">
          <div class="private-details__part">
            <span class="value">{{ resume.personalInfo.name }}</span>
            <span class="value">{{ resume.personalInfo.gender }}</span>
            <span class="value">{{ resume.personalInfo.age }}岁</span>
            <span class="value">{{ resume.personalInfo.applicationPosition }}</span>
          </div>
        </div>
        <div class="contact-details">
          <div class="contact-details__part">
            <span class="label">(+86)</span>
            <span class="value">{{ resume.personalInfo.phone }}</span>
          </div>
          <div class="contact-details__part">
            <span class="value">{{ resume.personalInfo.email }}</span>
          </div>
          <div class="contact-details__part">
            <span class="label">个人网站</span>
            <a :href="resume.personalInfo.website" target="_blank" class="value">{{ resume.personalInfo.website }}</a>
          </div>
        </div>

        <div class="contact-details">
          <div>
            <span class="label">政治面貌：</span>
            <span class="value">{{ resume.personalInfo.politicalStatus }}</span>
          </div>
          <div>
            <span class="label">学校：</span>
            <span class="value">{{ resume.personalInfo.university }}</span>
          </div>
          <div>
            <span class="label">专业：</span>
            <span class="value">{{ resume.personalInfo.major }}</span>
          </div>
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
        <div class="eduItem" v-for="edu in resume.education" :key="edu.id">
          <span>{{ edu.school }} ({{ edu.degree }})</span>
          <span>{{ edu.major }}</span>
          <b v-if="edu.startDate && edu.endDate">{{ edu.startDate }} 至 {{ edu.endDate }}</b>
        </div>
      </div>
    </div>

    <!-- 工作经历 -->
    <div class="section experience-section" v-if="resume.workExperience.length">
      <div class="section-title">工作经历</div>
      <ul class="section-content experience-content">
        <li class="item" v-for="work in resume.workExperience" :key="work.id">
          <div class="experience-content__intro">
            <span class="value">{{ work.company }}</span>
            <span class="value">{{ work.position }}</span>
            <span class="value">{{ work.startDate }} - {{ work.endDate }}</span>
          </div>
          <p v-html="marked(work.description)"></p>
        </li>
      </ul>
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
      <ul class="section-content experience-content">
        <li class="item" v-for="project in resume.projects" :key="project.id">
          <div class="experience-content__intro">
            <span class="value">{{ project.projectName }}</span>
            <span class="value">{{ project.role }}</span>
            <span class="value">{{ project.startDate }} - {{ project.endDate }}</span>
          </div>
          <p style="margin: 8px" v-html="marked(project.briefIntroduction)"></p>
          <ul class="experience-content__details">
            <li v-for="(desc, index) in project.description.split('\n')" :key="index" v-html="marked(desc)"></li>
          </ul>
        </li>
      </ul>
    </div>

    <!-- 荣誉奖项 -->
    <div class="section honors-section" v-if="resume.honors.length">
      <div class="section-title">荣誉奖项</div>
      <ul class="section-content experience-content">
        <li class="item" v-for="honor in resume.honors" :key="honor.id">
          <span class="value" style="font-weight: 600;">{{ honor.honorName }} ({{ honor.date }})</span>
          <p v-html="marked(honor.description)"></p>
        </li>
      </ul>
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

.contact-details {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  max-width: 80%;
  margin-bottom: 8px;
}

.private-details__part {
  color: #000;
  font-weight: bolder;
}

.private-details__part span:not(:last-child)::after {
  content: '-';
  color: #000;
  font-weight: bolder;
}

.contact-details__part {
  color: #808080;
  font-weight: bolder;
}

.contact-details__part:not(:last-child)::after {
  content: "|";
  color: #000;
  font-weight: bolder;
  margin: 0 5px;
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

.section-content .eduItem {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.section-content.experience-content {
  list-style-type: disc;
  padding-left: 20px;
}

.experience-content__intro {
  display: flex;
  justify-content: space-between;
  margin-bottom: 3px;
  color: #000;
  font-weight: 600;
}

.experience-content__details {
  list-style-type: circle;
  padding-left: 25px;
}

.section-content .item {
  margin-bottom: 5px;
}

/*计数器样式*/
@counter-style tech-counter {
  system: cyclic;
  /* 使用循环系统，当符号用完后从头开始 */
  symbols: "🏁" "🔤" "📦" "🗄️" "🔧" "🐙";
  /* 这里可以放置你喜欢的 Emoji */
  suffix: " ";
  /* 每个 Emoji 后面添加一个空格 */
}

.skills-list {
  list-style-type: tech-counter;
  padding-left: 25px;
}

.skills-list li {
  margin-bottom: 5px;
}

.self-evaluation {
  font-style: italic;
  margin-top: 10px;
  padding-left: 20px;
  font-weight: 600;
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>