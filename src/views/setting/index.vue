<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">必要设置</h2>

      <!-- 说明文字 -->
      <p class="tips">
        注意：此处调用接口使用的是 OpenAI 的接口格式
        （换言之，只要你的大模型接口厂商使用的是 OpenAI 格式，你填入都能正常调用接口）
        <span style="color:red">默认值不会改请不要动！！要是完全不会，就只填apikey就行了，点击链接前往获取key，填入即可</span>
      </p>
      <div class="input-group">
        <label for="api-url">大模型名称<span style="color:red">（不懂勿改）</span></label>
        <a-input id="api-url" v-model:value="settingsStore.modelName" placeholder="请输入模型名称" />
        <p class="tips">
          如果用我的反代地址，请使用阿里的大模型，如果不会配置，请勿修改，默认为"qwen-turbo"
          <a href="https://bailian.console.aliyun.com/#/model-market" target="_blank">
            查看阿里百炼模型大全
          </a>。
        </p>
      </div>

      <div class="input-group">
        <label for="api-key">API Key（使用大模型）</label>
        <a-input id="api-key" v-model:value="settingsStore.aliApiKey" placeholder="请输入 API Key" />
        <p class="tips">
          请填写 API Key 用于调用 AI 模型。如果下面使用的是我提供的反代地址，请前往阿里云获取
          <a href="https://bailian.console.aliyun.com/?apiKey=1#/api-key" target="_blank">阿里云百炼 API Key</a>。
        </p>
      </div>

      <div class="input-group">
        <label for="api-url">API URL<span style="color:red">（不懂勿改）</span></label>
        <a-input id="api-url" v-model:value="settingsStore.aliApiUrl" placeholder="请输入 API URL" />
        <p class="tips">
          请填写 API URL（经过反向代理，解决跨域问题），用于调用 AI 模型。或者直接使用我提供的反代地址：
          https://resumeai.404.pub/
          （该地址仅适用于阿里云百炼 API Key）。
          <a href="https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api" target="_blank">
            查看阿里百炼官方文档
          </a>。
        </p>
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
