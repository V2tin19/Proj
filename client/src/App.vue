<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { theme } from 'ant-design-vue';
import Header from "./components/Header/index.vue";
import { useResumeStore } from './store/useResumeStore';
import { useSettingsStore } from './store/useSettingsStore';
import { useBackendHealth } from './composables/useBackendHealth';

const settingsStore = useSettingsStore();
const { start: startHealthPolling } = useBackendHealth();

// 页面加载时初始化
onMounted(async () => {
  const resumeStore = useResumeStore();
  await resumeStore.initCheck();
  settingsStore.initTheme();
  startHealthPolling();
});

const antdThemeConfig = computed(() => ({
  algorithm: settingsStore.isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
  token: {
    colorPrimary: settingsStore.theme,
    borderRadius: 8,
  },
}));
</script>

<template>
  <a-config-provider :theme="antdThemeConfig">
    <div class="app-shell">
      <Header />
      <main class="app-content">
        <router-view v-slot="{ Component }">
          <keep-alive include="aiDeep">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </a-config-provider>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-content {
  min-height: calc(100vh - 72px);
}

@media (max-width: 768px) {
  .app-content {
    min-height: 100svh;
    padding-bottom: calc(76px + env(safe-area-inset-bottom));
  }
}
</style>
