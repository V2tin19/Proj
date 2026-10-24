<template>
  <div class="input-group">
    <label>服务端地址</label>
    <div class="server-row">
      <a-input
        v-model:value="serverUrlDraft"
        placeholder="如 http://192.168.1.10:8000(同源部署可留空)"
        allow-clear
      />
      <a-button type="primary" @click="saveServerUrl">保存</a-button>
    </div>
    <p class="field-tip">客户端连接的服务端;修改后立即生效,留空表示同源部署。</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { getServerBase, setServerBase } from '../../utils/auth';
import { useBackendHealth } from '../../composables/useBackendHealth';

const serverUrlDraft = ref<string>(getServerBase());
const { refresh: refreshHealth } = useBackendHealth();

const saveServerUrl = () => {
  setServerBase(serverUrlDraft.value);
  message.success('服务端地址已保存');
  // 换服务端后立刻重新探测连接状态
  refreshHealth();
};
</script>

<style scoped>
.input-group {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.server-row {
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
</style>
