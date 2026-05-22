<template>
  <header class="navbar">
    <nav>
      <ul>
        <li>
          <router-link to="/">
            <SvgIcon iconName="resume" />
            简历制作
          </router-link>
        </li>
        <li ref="templateStore">
          <router-link to="/template">
            <SvgIcon iconName="templateStore" />
            模板市场
          </router-link>
        </li>
        <li>
          <router-link to="/agent">
            <SvgIcon iconName="example" />
            简历智能体
          </router-link>
        </li>
        <li>
          <router-link to="/aiDeep">
            <SvgIcon iconName="ai" />
            AI深度交流
          </router-link>
        </li>
        <li ref="setting">
          <router-link to="/setting">
            <SvgIcon iconName="setting" />
            网站配置
          </router-link>
        </li>
      </ul>
    </nav>
  </header>

  <a-tour
    v-model:open="tourOpen"
    :steps="tourSteps"
    :mask="true"
    :next-button-props="{ children: '下一步' }"
    :prev-button-props="{ children: '上一步' }"
    :finish-button-props="{ children: '完成' }"
    @finish="handleFinish"
    @close="handleFinish"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { TourProps } from "ant-design-vue";
import SvgIcon from "../SvgIcon.vue";
import { useResumeStore } from "../../store/useResumeStore";

const store = useResumeStore();
const setting = ref(null);
const templateStore = ref(null);
const tourOpen = ref(false);

const tourSteps: TourProps["steps"] = [
  {
    title: "网站配置",
    description: "请先进入网站配置，补充模型接口等基础信息，否则 AI 能力无法稳定使用。",
    target: () => setting.value,
  },
  {
    title: "选择模板",
    description: "然后进入模板市场，挑选适合自己的简历模板。",
    target: () => templateStore.value,
  }
];

const handleFinish = () => {
  tourOpen.value = false;
};

onMounted(() => {
  if (store.isFirstVisit) {
    tourOpen.value = true;
  }
});
</script>

<style scoped>
.navbar {
  background:
    linear-gradient(90deg, rgba(4, 7, 13, 0.98), rgba(13, 20, 32, 0.96) 40%, rgba(15, 31, 61, 0.95) 100%);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 16px 40px var(--shadow-color);
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.navbar nav ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
}

.navbar nav ul li {
  float: left;
}

.navbar nav ul li a {
  display: block;
  color: var(--text-color);
  text-align: center;
  font-size: 17px;
  padding: 17px 16px;
  text-decoration: none;
  transition: all 0.22s;
  border-radius: 14px;
  margin: 10px 6px;
}

.navbar nav ul li a:hover {
  background-color: rgba(59, 108, 255, 0.14);
  color: #ffffff;
}

.navbar nav ul li .router-link-active {
  background: rgba(59, 108, 255, 0.2);
  color: #ffffff;
}
</style>
