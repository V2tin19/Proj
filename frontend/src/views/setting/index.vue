<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">必要设置</h2>

      <!-- 说明文字 -->
      <p class="tips">
        大模型调用相关的 API Key、API URL、模型名称等配置已迁移至后端环境变量管理。
        如需调整，请修改后端 <code>.env</code> 文件并重启后端服务。
      </p>

      <!-- 主题切换 -->
      <div class="input-group">
        <label>主题模式</label>
        <a-switch
          v-model:checked="settingsStore.isDark"
          checked-children="深色"
          un-checked-children="浅色"
          @change="settingsStore.toggleTheme"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../../store/useSettingsStore';

const settingsStore = useSettingsStore();
</script>

<style scoped>
.settings-container {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.settings-card {
  width: 100%;
  max-width: 600px;
  background:
    linear-gradient(180deg, rgba(16, 23, 34, 0.96), rgba(10, 17, 27, 0.98));
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

.title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
  text-align: center;
  color: var(--primary-color);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}

.tips {
  font-size: 13px;
  background: rgba(60, 80, 120, 0.1);
  padding: 10px;
  border-radius: 8px;
  color: var(--text-muted);
  line-height: 1.5;
  text-align: justify;
  border: 1px solid var(--border-color);
}

.tips code {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 16px 12px;
  }

  .settings-card {
    padding: 16px;
    border-radius: 14px;
  }

  .title {
    font-size: 20px;
    margin-bottom: 16px;
  }

  .tips {
    font-size: 12px;
    text-align: left;
    word-break: break-word;
  }
}
</style>
