<template>
  <div class="input-group">
    <label>主题外观</label>
    <div class="theme-row">
      <a-radio-group
        :value="settingsStore.themeMode"
        button-style="solid"
        size="middle"
        @change="(e: any) => settingsStore.setThemeMode(e.target.value)"
      >
        <a-radio-button value="light">
          <span>☀️ 浅色</span>
        </a-radio-button>
        <a-radio-button value="dark">
          <span>🌙 深色</span>
        </a-radio-button>
        <a-radio-button value="system">
          <span>💻 跟随系统</span>
        </a-radio-button>
      </a-radio-group>
    </div>
    <p class="field-tip">
      {{
        settingsStore.themeMode === 'system'
          ? `跟随系统模式（系统当前偏好: ${settingsStore.isDark ? '深色' : '浅色'}）`
          : settingsStore.themeMode === 'dark'
          ? '当前已固定为深色模式'
          : '当前已固定为浅色模式'
      }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../../store/useSettingsStore';

const settingsStore = useSettingsStore();
</script>

<style scoped>
.input-group {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.theme-row {
  display: flex;
  align-items: center;
  margin-top: 2px;
}

.field-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
}

label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}
</style>
