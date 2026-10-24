<template>
  <a-drawer
    :open="open"
    title="账号与设置"
    placement="right"
    :width="drawerWidth"
    destroy-on-close
    @close="emit('update:open', false)"
  >
    <AccountPanel @session-change="emit('session-change')" />
    <ConnectionPanel />
    <ThemePanel />
    <p class="tips">
      大模型调用相关的 API Key、API URL、模型名称等配置由服务端统一管理。
    </p>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import AccountPanel from './settings/AccountPanel.vue';
import ConnectionPanel from './settings/ConnectionPanel.vue';
import ThemePanel from './settings/ThemePanel.vue';

defineProps<{ open: boolean }>();
const emit = defineEmits<{
  (e: 'update:open', value: boolean): void;
  (e: 'session-change'): void;
}>();

const drawerWidth = computed(() =>
  Math.min(420, typeof window !== 'undefined' ? window.innerWidth - 24 : 420)
);
</script>

<style scoped>
.tips {
  font-size: 13px;
  background: rgba(60, 80, 120, 0.08);
  padding: 12px;
  border-radius: 8px;
  color: var(--text-muted);
  line-height: 1.5;
  text-align: justify;
  border: 1px solid var(--border-color);
  margin: 0;
}
</style>
