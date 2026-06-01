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
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 72px;
  padding: 0 16px;
}

.navbar nav {
  width: min(100%, 980px);
}

.navbar nav ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.navbar nav ul li a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: var(--text-color);
  text-align: center;
  font-size: 17px;
  min-height: 48px;
  padding: 0 14px;
  text-decoration: none;
  transition: all 0.22s;
  border-radius: 14px;
  white-space: nowrap;
}

.navbar nav ul li a:hover {
  background-color: rgba(59, 108, 255, 0.14);
  color: #ffffff;
}

.navbar nav ul li .router-link-active {
  background: rgba(59, 108, 255, 0.2);
  color: #ffffff;
}

.navbar :deep(.svg-icon) {
  font-size: 18px;
}

@media (max-width: 768px) {
  .navbar {
    position: fixed;
    inset: auto 0 0 0;
    min-height: calc(64px + env(safe-area-inset-bottom));
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
    border-top: 1px solid var(--border-color);
    border-bottom: 0;
    box-shadow: 0 -14px 32px var(--shadow-color);
  }

  .navbar nav {
    width: 100%;
  }

  .navbar nav ul {
    justify-content: space-between;
    gap: 2px;
  }

  .navbar nav ul li {
    flex: 1;
    min-width: 0;
  }

  .navbar nav ul li a {
    width: 100%;
    min-height: 52px;
    padding: 6px 2px;
    flex-direction: column;
    gap: 4px;
    border-radius: 12px;
    font-size: 11px;
    line-height: 1.15;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .navbar :deep(.svg-icon) {
    font-size: 20px;
  }
}
</style>
