<template>
  <div class="settings-container">
    <a-card class="settings-card" :bordered="false">
      <h2 class="title">账号与设置</h2>

      <!-- 登录状态 -->
      <div class="input-group">
        <label>当前账号</label>
        <div v-if="session" class="session-row">
          <div class="session-info">
            <strong>{{ session.username }}</strong>
            <a-tag :color="session.role === 'admin' ? 'gold' : 'blue'" class="role-tag">
              {{ session.role === 'admin' ? '运营者' : '用户' }}
            </a-tag>
          </div>
          <a-button danger ghost size="small" @click="handleLogout">退出登录</a-button>
        </div>
        <div v-else class="session-row">
          <span class="muted">未登录(匿名模式,功能可能受限)</span>
          <a-button type="primary" size="small" @click="goAuth">注册 / 登录</a-button>
        </div>
      </div>

      <!-- 服务端地址 -->
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
        <p class="field-tip">C/S 模式下客户端连接的服务端;修改后立即生效。</p>
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

      <!-- 说明 -->
      <p class="tips">
        大模型调用相关的 API Key、API URL、模型名称等配置由服务端统一管理。
      </p>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { useSettingsStore } from '../../store/useSettingsStore';
import { logoutAccount } from '../../api/agentAPI';
import { clearSession, getSessionUser, getServerBase, setServerBase } from '../../utils/auth';

const router = useRouter();
const settingsStore = useSettingsStore();

// 直接读 storage;退出/登录后通过跳转刷新视图
const session = computed(() => getSessionUser());
const serverUrlDraft = ref<string>(getServerBase());

const saveServerUrl = () => {
  setServerBase(serverUrlDraft.value);
  message.success('服务端地址已保存');
};

const handleLogout = async () => {
  await logoutAccount();
  message.success('已退出登录');
  router.push({ name: 'auth' });
};

const goAuth = () => {
  clearSession();
  router.push({ name: 'auth' });
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

.session-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-tag {
  margin: 0;
}

.server-row {
  display: flex;
  gap: 8px;
}

.muted {
  color: var(--text-muted);
  font-size: 13px;
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
