<script setup lang="ts">
import Header from "./components/Header/index.vue";
import { useResumeStore } from './store/useResumeStore';
import { useSettingsStore } from './store/useSettingsStore';
import { onMounted } from 'vue';
const settingsStore = useSettingsStore();

// 页面加载时初始化
onMounted(async () => {
  const resumeStore = useResumeStore();
  await resumeStore.initCheck();
  settingsStore.initTheme();
});
</script>

<template>
  <a-config-provider :theme="{
    token: {
      colorPrimary: settingsStore.theme,
    },
  }">
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
