<template>
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
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { logoutAccount } from '../../api/agentAPI';
import { clearSession, getSessionUser } from '../../utils/auth';

const emit = defineEmits<{ (e: 'session-change'): void }>();
const router = useRouter();
// 每次挂载时读取(抽屉 destroyOnClose / 页面路由进入都会重新挂载)
const session = ref(getSessionUser());

const handleLogout = async () => {
  await logoutAccount();
  session.value = null;
  emit('session-change');
  message.success('已退出登录');
  router.push({ name: 'auth' });
};

const goAuth = () => {
  clearSession();
  router.push({ name: 'auth' });
};
</script>

<style scoped>
.input-group {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.muted {
  color: var(--text-muted);
  font-size: 13px;
}

label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}
</style>
