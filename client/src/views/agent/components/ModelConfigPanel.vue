<template>
  <div class="model-config">
    <a-alert v-if="!isServerReachable" type="warning" show-icon class="config-alert">
      <template #message>服务端离线,无法管理模型配置</template>
    </a-alert>

    <template v-else>
      <!-- 桌面端:提示内置管理员账号(本机服务端由桌面壳自动拉起) -->
      <a-alert
        v-if="builtinAdmin && !isAdminSession"
        type="info"
        show-icon
        class="config-alert"
        message="本机服务端内置管理员账号"
      >
        <template #description>
          用户名 <code>{{ builtinAdmin.user }}</code> · 初始密码
          <code>{{ builtinAdmin.password }}</code>(登录后可在「模型服务」配置模型;密码同步保存在数据目录
          admin-credentials.txt)。
        </template>
      </a-alert>

      <div class="form-section">
        <div class="section-title"><span>当前模型服务</span></div>
        <div class="status-grid">
          <div class="status-item">
            <span>状态</span>
            <a-tag :color="providerColor">{{ providerText }}</a-tag>
          </div>
          <div class="status-item">
            <span>配置来源</span>
            <a-tag>{{ config.source === 'runtime' ? '在线配置' : '服务端 .env' }}</a-tag>
          </div>
          <div class="status-item">
            <span>API Key</span>
            <strong>{{ config.hasKey ? config.keyMasked : '未配置' }}</strong>
          </div>
        </div>
        <p class="field-tip">
          保存后立即对简历生成与 AI 对话生效,无需重启服务;留空 API Key 表示沿用已保存的 Key。
        </p>
      </div>

      <div class="form-section">
        <div class="section-title"><span>模型接口配置</span></div>
        <div class="grid-two">
          <a-input v-model:value="form.apiUrl" placeholder="API URL,如 https://api.deepseek.com/v1/chat/completions" addon-before="API URL" />
          <a-input v-model:value="form.model" placeholder="模型名,如 qwen-plus / deepseek-chat" addon-before="模型" />
        </div>
        <a-input-password
          v-model:value="form.apiKey"
          :placeholder="config.hasKey ? `已配置(${config.keyMasked}),留空表示不修改` : 'API Key'"
          addon-before="API Key"
          style="margin-top: 12px;"
        />

        <div class="action-row">
          <a-button :loading="testing" @click="handleTest">测试连接</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">保存并生效</a-button>
          <a-popconfirm
            v-if="config.source === 'runtime'"
            title="清除在线配置,恢复为服务端 .env 的默认值?"
            ok-text="恢复默认"
            cancel-text="取消"
            @confirm="handleReset"
          >
            <a-button danger ghost>恢复默认(.env)</a-button>
          </a-popconfirm>
        </div>
      </div>

      <div v-if="testResult" class="form-section" :class="testResult.ok ? 'test-ok' : 'test-fail'">
        <div class="section-title">
          <span>连接测试</span>
          <a-tag :color="testResult.ok ? 'success' : 'error'">{{ testResult.ok ? '成功' : '失败' }}</a-tag>
        </div>
        <p class="field-tip">
          {{ testResult.message }}
          <template v-if="testResult.ok && testResult.latencyMs"> · 耗时 {{ testResult.latencyMs }}ms</template>
        </p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import {
  clearLlmConfig,
  getLlmConfig,
  saveLlmConfig,
  testLlmConfig,
  type LlmConfig,
  type LlmTestResult
} from '../../../api/agentAPI';
import { useBackendHealth } from '../../../composables/useBackendHealth';
import { getSessionUser, isTauriEnv } from '../../../utils/auth';

const health = useBackendHealth();
const isServerReachable = computed(() => health.status.value !== 'down');
const isAdminSession = getSessionUser()?.role === 'admin';

// 桌面端内置管理员账号(壳拉起后端时生成,见 Rust ensure_admin_credentials)
const builtinAdmin = ref<{ user: string; password: string } | null>(null);
if (isTauriEnv()) {
  void (async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const info = await invoke<{ managed: boolean; adminUser: string; adminPassword: string }>('backend_info');
      if (info?.managed && info.adminPassword) {
        builtinAdmin.value = { user: info.adminUser, password: info.adminPassword };
      }
    } catch {
      /* 非 Tauri 环境或命令不可用,忽略 */
    }
  })();
}

const providerText = computed(() => {
  if (health.status.value === 'down') return '离线';
  return health.info.value?.provider === 'llm-configured' ? '已连接模型' : '本地回退';
});
const providerColor = computed(() => {
  if (health.status.value === 'down') return 'error';
  return health.info.value?.provider === 'llm-configured' ? 'success' : 'warning';
});

const config = ref<LlmConfig>({ apiUrl: '', model: '', hasKey: false, keyMasked: '', source: 'env' });
const form = reactive({ apiUrl: '', apiKey: '', model: '' });
const testing = ref(false);
const saving = ref(false);
const testResult = ref<LlmTestResult | null>(null);

const loadConfig = async () => {
  try {
    config.value = await getLlmConfig();
    form.apiUrl = config.value.apiUrl;
    form.model = config.value.model;
    form.apiKey = '';
  } catch (error) {
    console.error(error);
    message.error((error as Error).message || '配置读取失败');
  }
};

const handleTest = async () => {
  if (!form.apiUrl.trim() || !form.model.trim()) {
    message.warning('请先填写 API URL 与模型名');
    return;
  }
  testing.value = true;
  testResult.value = null;
  try {
    // 用表单候选值测试:填了 Key 用填的,没填则用已保存的(后端兜底)
    testResult.value = await testLlmConfig({
      apiUrl: form.apiUrl.trim(),
      apiKey: form.apiKey.trim(),
      model: form.model.trim()
    });
  } catch (error) {
    message.error((error as Error).message || '测试请求失败');
  } finally {
    testing.value = false;
  }
};

const handleSave = async () => {
  if (!form.apiUrl.trim() || !form.model.trim()) {
    message.warning('请填写 API URL 与模型名');
    return;
  }
  saving.value = true;
  try {
    config.value = await saveLlmConfig({
      apiUrl: form.apiUrl.trim(),
      apiKey: form.apiKey.trim(),
      model: form.model.trim()
    });
    form.apiKey = '';
    message.success('模型配置已保存并生效');
    health.refresh();
  } catch (error) {
    message.error((error as Error).message || '保存失败');
  } finally {
    saving.value = false;
  }
};

const handleReset = async () => {
  try {
    config.value = await clearLlmConfig();
    form.apiUrl = config.value.apiUrl;
    form.model = config.value.model;
    form.apiKey = '';
    testResult.value = null;
    message.success('已恢复为服务端默认配置');
    health.refresh();
  } catch (error) {
    message.error((error as Error).message || '恢复失败');
  }
};

onMounted(loadConfig);
</script>

<style scoped>
.model-config {
  display: flex;
  flex-direction: column;
}

.config-alert {
  margin-bottom: 16px;
}

.form-section {
  margin-bottom: 20px;
  padding: 18px;
  border-radius: 16px;
  background: var(--inset-bg);
  border: 1px solid var(--border-color);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--text-color);
  font-weight: 600;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.status-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--inset-bg-strong);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-item span {
  color: var(--text-muted);
  font-size: 12px;
}

.status-item strong {
  color: var(--text-color);
  font-size: 14px;
  word-break: break-all;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.field-tip {
  margin: 10px 0 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.test-ok {
  border-color: rgba(82, 196, 26, 0.4);
}

.test-fail {
  border-color: rgba(255, 77, 79, 0.4);
}

.form-section :deep(.ant-input),
.form-section :deep(.ant-input-affix-wrapper) {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .grid-two,
  .status-grid {
    grid-template-columns: 1fr;
  }

  .action-row {
    flex-direction: column;
  }

  .action-row :deep(.ant-btn) {
    width: 100%;
  }
}
</style>
