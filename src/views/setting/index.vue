<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">必要设置</h2>

      <!-- 说明文字 -->
      <p class="tips">
        注意：此处调用接口使用的是 OpenAI 的接口格式
        （换言之，只要你的大模型接口厂商使用的是 OpenAI 格式，你填入都能正常调用接口）
        <span style="color:red">不会配置就选下面的预设，或只填 API Key 即可</span>
      </p>

      <!-- 平台预设按钮 -->
      <div class="preset-buttons">
        <a-button
          v-for="preset in presets"
          :key="preset.name"
          :type="currentPreset === preset.name ? 'primary' : 'default'"
          @click="applyPreset(preset)"
        >
          {{ preset.name }}
        </a-button>
      </div>

      <div class="input-group">
        <label for="model-name">大模型名称<span style="color:red">（不懂勿改）</span></label>
        <a-input id="model-name" v-model:value="settingsStore.modelName" placeholder="请输入模型名称" />
        <p class="tips">
          模型名称示例：qwen-turbo、qwen-plus、deepseek-chat、gpt-3.5-turbo
        </p>
      </div>

      <div class="input-group">
        <label for="api-key">API Key（使用大模型）</label>
        <a-input id="api-key" v-model:value="settingsStore.aliApiKey" placeholder="请输入 API Key" />
        <p class="tips">
          请填写 API Key 用于调用 AI 模型。
          <a href="https://bailian.console.aliyun.com/?apiKey=1#/api-key" target="_blank">阿里云百炼 API Key</a>
          |
          <a href="https://platform.deepseek.com/api_keys" target="_blank">DeepSeek API Key</a>
        </p>
      </div>

      <div class="input-group">
        <label for="api-url">API URL<span style="color:red">（不懂勿改）</span></label>
        <a-input id="api-url" v-model:value="settingsStore.aliApiUrl" placeholder="请输入 API URL" />
        <p class="tips">
          必须以 <code>/v1/chat/completions</code> 结尾。常用地址：
          <br>阿里云：<code>https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions</code>
          <br>DeepSeek：<code>https://api.deepseek.com/v1/chat/completions</code>
        </p>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSettingsStore } from '../../store/useSettingsStore';

const settingsStore = useSettingsStore();
const currentPreset = ref('');

const presets = [
  {
    name: '阿里云百炼',
    modelName: 'qwen-turbo',
    aliApiUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  },
  {
    name: 'DeepSeek',
    modelName: 'deepseek-chat',
    aliApiUrl: 'https://api.deepseek.com/v1/chat/completions',
  },
];

const applyPreset = (preset: typeof presets[0]) => {
  currentPreset.value = preset.name;
  settingsStore.modelName = preset.modelName;
  settingsStore.aliApiUrl = preset.aliApiUrl;
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

.preset-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
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

.tips a {
  color: var(--primary-color);
  font-weight: 600;
  text-decoration: none;
  transition: color 0.3s;
}

.tips a:hover {
  color: var(--primary-color-hover);
  text-decoration: underline;
}
</style>
