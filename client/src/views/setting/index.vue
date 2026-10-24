<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">账号与设置</h2>
      <AccountPanel />
      <ConnectionPanel />
      <ThemePanel />
      <p class="tips">
        大模型调用相关的 API Key、API URL、模型名称等配置由服务端统一管理。
      </p>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import AccountPanel from '../../components/settings/AccountPanel.vue';
import ConnectionPanel from '../../components/settings/ConnectionPanel.vue';
import ThemePanel from '../../components/settings/ThemePanel.vue';
</script>

<style scoped>
.settings-container {
  display: flex;
  justify-content: center;
  padding: 32px 16px;
  min-height: calc(100vh - 72px);
}

.settings-card {
  width: 100%;
  max-width: 640px;
  background: var(--bg-card-color);
  border-radius: 16px;
  box-shadow: 0 16px 40px var(--shadow-color);
  border: 1px solid var(--border-color);
  padding: 24px;
  height: fit-content;
}

.title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 24px;
  color: var(--text-color);
}

.tips {
  font-size: 13px;
  background: rgba(60, 80, 120, 0.08);
  padding: 12px;
  border-radius: 8px;
  color: var(--text-muted);
  line-height: 1.5;
  text-align: justify;
  border: 1px solid var(--border-color);
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
