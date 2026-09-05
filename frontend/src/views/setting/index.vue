<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">必要设置</h2>

      <!-- 说明文字 -->
      <p class="tips">
        大模型调用相关的 API Key、API URL、模型名称等配置已迁移至后端环境变量管理。
        如需调整，请修改后端 <code>.env</code> 文件并重启后端服务。
      </p>

      <!-- 访问口令 -->
      <div class="input-group">
        <label>访问口令（X-Access-Code）</label>
        <div class="access-code-row">
          <a-input-password
            v-model:value="accessCodeDraft"
            placeholder="后端 .env 设置 ACCESS_CODE 后必填"
            allow-clear
          />
          <a-button type="primary" @click="saveAccessCode">保存</a-button>
        </div>
        <p class="field-tip">
          启用访问控制后,所有 AI 接口需要该口令;保存后立即生效。
        </p>
      </div>

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
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { useSettingsStore } from '../../store/useSettingsStore';

const settingsStore = useSettingsStore();
const accessCodeDraft = ref<string>(settingsStore.accessCode);

const saveAccessCode = () => {
  settingsStore.updateAccessCode(accessCodeDraft.value);
  message.success(accessCodeDraft.value ? '访问口令已保存' : '访问口令已清除');
};
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

.access-code-row {
  display: flex;
  gap: 8px;
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
