<template>
  <div class="resume-container" :style="colorShadesStyle">
    <!-- 个人信息 -->
    <div class="personal-info">
      <div class="personal-details">
        <div class="detail-row">
          <div class="detail-item name">
            <span class="value">{{ resume.personalInfo.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">性别：</span>
            <span class="value">{{ resume.personalInfo.gender }}</span>
          </div>
          <div class="detail-item">
            <span class="label">年龄：</span>
            <span class="value">{{ resume.personalInfo.age }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">政治面貌：</span>
            <span class="value">{{ resume.personalInfo.politicalStatus }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">电话：</span>
            <span class="value">{{ resume.personalInfo.phone }}</span>
          </div>
          <div class="detail-item">
            <span class="label">邮箱：</span>
            <span class="value">{{ resume.personalInfo.email }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">学校：</span>
            <span class="value">{{ resume.personalInfo.university }}</span>
          </div>
          <div class="detail-item">
            <span class="label">专业：</span>
            <span class="value">{{ resume.personalInfo.major }}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">网站：</span>
            <a :href="resume.personalInfo.website" target="_blank" class="value">{{ resume.personalInfo.website }}</a>
          </div>
        </div>
      </div>
      <div class="profile-image">
        <img :src="resume.personalInfo.avatar" alt="个人照片">
      </div>
    </div>

    <!-- 荣誉奖项、复用skills样式 -->
    <div class="section skills-section" v-if="resume.honors.length">
      <div class="section-title">荣誉奖项</div>
      <ul class="skills-list">
        <li v-for="honor in resume.honors" :key="honor.id" v-html="marked(honor.honorName)"></li>
      </ul>
    </div>

    <!-- 在校经历 -->
    <div class="section education-section" v-if="resume.education.length">
      <div class="section-title">教育经历</div>
      <div class="section-content">
        <div class="item" v-for="edu in resume.education" :key="edu.id">
          <p class="school">
            <span>{{ edu.school }}({{ edu.degree }})</span>
            <span>{{ edu.major }}</span>
            <b v-if="edu.startDate && edu.endDate">{{ edu.startDate }} 至 {{ edu.endDate }}</b>
            <!-- 空格 -->
          </p>
        </div>
      </div>
    </div>


    <!-- 技能特长 -->
    <div class="section skills-section" v-if="resume.skills.length">
      <div class="section-title">技能特长</div>
      <ul class="skills-list">
        <li v-for="skill in resume.skills" :key="skill.id" v-html="marked(skill.skillName)"></li>
      </ul>
    </div>
    <!-- 工作/实习经历 -->
    <div class="section experience-section" v-if="resume.workExperience.length">
      <div class="section-title">工作/实习经历</div>
      <div class="section-content">
        <div class="item" v-for="work in resume.workExperience" :key="work.id">
          <div class="subtitle">
            <div class="work-header">
              <span>{{ work.company }}</span>
              <span>{{ work.position }}</span>
              <span>{{ work.startDate }} 至 {{ work.endDate }}</span>
            </div>
          </div>
          <ul>
            <li v-for="(desc, index) in work.description.split('\n')" :key="index" v-html="marked(desc)"></li>
          </ul>
        </div>
      </div>
    </div>



    <!-- 项目经验 -->
    <div class="section projects-section" v-if="resume.projects.length">
      <div class="section-title">项目经验</div>
      <div class="section-content">
        <div class="item" v-for="project in resume.projects" :key="project.id">
          <div class="subtitle">
            <div class="project-header">
              <span>{{ project.projectName }}</span>
              <span>{{ project.role }}</span>
              <span>{{ project.startDate }} <span v-if="project.startDate && project.endDate">至</span> {{
                project.endDate }}</span>
            </div>
            <hr>
            <p class="project-introduction" v-html="marked(project.briefIntroduction)"></p>
          </div>
          <ul>
            <li v-for="(desc, index) in project.description.split('\n')" :key="index" v-html="marked(desc)"></li>
          </ul>
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
import { marked } from 'marked';
import type { ColorShades } from '../../types/color';
// 接受父组件主题色
const props = defineProps<{
  colorShades: ColorShades;
}>();

// 动态生成 CSS 变量的样式
const colorShadesStyle = computed(() => {
  return {
    '--color-lighter': props.colorShades.lighter,
    '--color-light': props.colorShades.light,
    '--color-base': props.colorShades.base,
    '--color-dark': props.colorShades.dark,
    '--color-darker': props.colorShades.darker,
    '--color-deepest': props.colorShades.deepest
  };
});
// 引入引用的store
const resumeStore = useResumeStore();

// 使用计算属性来获取store中的数据
const resume = computed(() => resumeStore.$state);

</script>
<!-- 引入外部css -->
<style scoped>
@import './assets/style.css';

/* 颜色相关的css放入style */
.section-title {
  width: 100%;
  color: var(--color-darker);
  background-color: var(--color-lighter);
  font-size: 18px;
  padding: 10px;
  font-weight: bold;
  border-left: 5px solid var(--color-base);
  margin-bottom: 10px;
  box-sizing: border-box;
}

:deep(strong) {
  color: var(--color-base) !important;
}
</style>