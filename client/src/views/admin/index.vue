<template>
  <div class="admin-page">
    <div class="admin-shell">
      <div class="admin-header">
        <div>
          <h1>运营后台</h1>
          <p>用户管理、使用统计与审计日志;仅运营者账号可见。</p>
        </div>
        <a-button @click="openChangeMyPassword">修改我的密码</a-button>
      </div>

      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="overview" tab="概览">
          <a-spin :spinning="statsLoading">
            <div class="stat-cards">
              <div class="stat-card">
                <span>注册用户</span>
                <strong>{{ stats?.last30Days.userTotal ?? '-' }}</strong>
              </div>
              <div class="stat-card">
                <span>已禁用</span>
                <strong>{{ stats?.last30Days.userDisabled ?? '-' }}</strong>
              </div>
              <div class="stat-card">
                <span>近30天生成</span>
                <strong>{{ stats?.last30Days.generate ?? 0 }}</strong>
              </div>
              <div class="stat-card">
                <span>近30天对话</span>
                <strong>{{ stats?.last30Days.chat ?? 0 }}</strong>
              </div>
              <div class="stat-card">
                <span>近30天导出</span>
                <strong>{{ stats?.last30Days.export_docx ?? 0 }}</strong>
              </div>
            </div>

            <div class="panel-grid">
              <div class="panel">
                <h3>近14天生成趋势</h3>
                <div v-if="dailyBars.length" class="bar-chart">
                  <div v-for="bar in dailyBars" :key="bar.day" class="bar-col" :title="`${bar.day}: ${bar.count} 次`">
                    <div class="bar" :style="{ height: `${bar.height}%` }" />
                    <span class="bar-label">{{ bar.label }}</span>
                  </div>
                </div>
                <a-empty v-else description="暂无生成记录" />
              </div>

              <div class="panel">
                <h3>生成来源(近30天)</h3>
                <div v-if="providerTotal > 0" class="provider-rows">
                  <div v-for="(count, provider) in stats?.generateProviders" :key="provider" class="provider-row">
                    <a-tag :color="provider === 'llm' ? 'success' : 'warning'">
                      {{ provider === 'llm' ? '模型生成' : provider || '未知' }}
                    </a-tag>
                    <div class="provider-track">
                      <div class="provider-fill" :style="{ width: `${(count / providerTotal) * 100}%` }" />
                    </div>
                    <span class="provider-count">{{ count }}</span>
                  </div>
                </div>
                <a-empty v-else description="暂无生成记录" />
              </div>

              <div class="panel">
                <h3>活跃用户(近30天)</h3>
                <table v-if="stats?.topUsers?.length" class="mini-table">
                  <tr v-for="u in stats.topUsers" :key="u.username">
                    <td>{{ u.username }}</td>
                    <td class="num">{{ u.events }} 次操作</td>
                  </tr>
                </table>
                <a-empty v-else description="暂无活跃用户" />
              </div>
            </div>
          </a-spin>
        </a-tab-pane>

        <a-tab-pane key="users" tab="用户管理">
          <a-table
            :data-source="users"
            :loading="usersLoading"
            :pagination="false"
            row-key="id"
            size="middle"
          >
            <a-table-column title="用户名" data-index="username" />
            <a-table-column title="角色" data-index="role" :width="90">
              <template #default="{ text }">
                <a-tag :color="text === 'admin' ? 'gold' : 'blue'">{{ text === 'admin' ? '运营者' : '用户' }}</a-tag>
              </template>
            </a-table-column>
            <a-table-column title="状态" :width="90">
              <template #default="{ record }">
                <a-tag :color="record.disabled ? 'error' : 'success'">{{ record.disabled ? '已禁用' : '正常' }}</a-tag>
              </template>
            </a-table-column>
            <a-table-column title="活跃会话" data-index="activeTokens" :width="90" />
            <a-table-column title="注册时间" data-index="createdAt" :width="170">
              <template #default="{ text }">{{ formatTime(text) }}</template>
            </a-table-column>
            <a-table-column title="操作" :width="200">
              <template #default="{ record }">
                <a-space>
                  <a-popconfirm
                    :title="record.disabled ? '恢复该账号的登录与使用?' : '禁用后该账号立即失效,确定?'"
                    :ok-text="record.disabled ? '启用' : '禁用'"
                    cancel-text="取消"
                    @confirm="toggleDisabled(record)"
                  >
                    <a-button size="small" :danger="!record.disabled" :ghost="!record.disabled">
                      {{ record.disabled ? '启用' : '禁用' }}
                    </a-button>
                  </a-popconfirm>
                  <a-button size="small" @click="openResetPassword(record)">重置密码</a-button>
                </a-space>
              </template>
            </a-table-column>
          </a-table>
        </a-tab-pane>

        <a-tab-pane key="audit" tab="审计日志">
          <a-table
            :data-source="events"
            :loading="eventsLoading"
            :pagination="false"
            row-key="id"
            size="middle"
          >
            <a-table-column title="时间" data-index="at" :width="170">
              <template #default="{ text }">{{ formatTime(text) }}</template>
            </a-table-column>
            <a-table-column title="用户" data-index="username" :width="130" />
            <a-table-column title="类型" :width="140">
              <template #default="{ record }">
                <a-tag :color="eventColor(record.type)">{{ eventLabel(record.type) }}</a-tag>
              </template>
            </a-table-column>
            <a-table-column title="详情" data-index="detail" />
          </a-table>
          <div class="load-more">
            <a-button :loading="eventsLoading" @click="loadMoreEvents">加载更多</a-button>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- 重置密码 -->
    <a-modal v-model:open="resetModalOpen" :title="`重置密码:${resetTarget?.username ?? ''}`" ok-text="重置" cancel-text="取消" @ok="confirmResetPassword">
      <a-input-password v-model:value="resetDraft" placeholder="新密码(≥8位,含字母和数字)" />
    </a-modal>

    <!-- 修改我的密码 -->
    <a-modal v-model:open="myPwdModalOpen" title="修改我的密码" ok-text="修改" cancel-text="取消" @ok="confirmChangeMyPassword">
      <a-space direction="vertical" style="width: 100%">
        <a-input-password v-model:value="myOldPwd" placeholder="原密码" />
        <a-input-password v-model:value="myNewPwd" placeholder="新密码(≥8位,含字母和数字)" />
      </a-space>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { message } from 'ant-design-vue';
import {
  changeMyPassword,
  fetchAdminEvents,
  fetchAdminStats,
  fetchAdminUsers,
  resetUserPassword,
  setUserDisabled,
  type AdminEvent,
  type AdminStats,
  type AdminUser
} from '../../api/agentAPI';

const activeTab = ref('overview');
const stats = ref<AdminStats | null>(null);
const statsLoading = ref(false);
const users = ref<AdminUser[]>([]);
const usersLoading = ref(false);
const events = ref<AdminEvent[]>([]);
const eventsLoading = ref(false);
const eventOffset = ref(0);
const PAGE_SIZE = 100;

const loadStats = async () => {
  statsLoading.value = true;
  try {
    stats.value = await fetchAdminStats();
  } catch (error) {
    message.error((error as Error).message || '统计加载失败');
  } finally {
    statsLoading.value = false;
  }
};

const loadUsers = async () => {
  usersLoading.value = true;
  try {
    users.value = await fetchAdminUsers();
  } catch (error) {
    message.error((error as Error).message || '用户列表加载失败');
  } finally {
    usersLoading.value = false;
  }
};

const loadEvents = async (append = false) => {
  eventsLoading.value = true;
  try {
    const batch = await fetchAdminEvents(PAGE_SIZE, eventOffset.value);
    events.value = append ? [...events.value, ...batch] : batch;
    eventOffset.value += batch.length;
  } catch (error) {
    message.error((error as Error).message || '审计日志加载失败');
  } finally {
    eventsLoading.value = false;
  }
};

const loadMoreEvents = () => loadEvents(true);

const dailyBars = computed(() => {
  const rows = stats.value?.generateDaily14d ?? [];
  const max = Math.max(1, ...rows.map((r) => r.count));
  return rows.map((r) => ({
    day: r.day,
    label: r.day.slice(5).replace('-', '/'),
    count: r.count,
    height: Math.max(6, Math.round((r.count / max) * 100))
  }));
});

const providerTotal = computed(() =>
  Object.values(stats.value?.generateProviders ?? {}).reduce((a, b) => a + b, 0)
);

const toggleDisabled = async (record: AdminUser) => {
  try {
    users.value = await setUserDisabled(record.id, !record.disabled);
    message.success(record.disabled ? '已启用' : '已禁用');
  } catch (error) {
    message.error((error as Error).message || '操作失败');
  }
};

const resetModalOpen = ref(false);
const resetTarget = ref<AdminUser | null>(null);
const resetDraft = ref('');

const openResetPassword = (record: AdminUser) => {
  resetTarget.value = record;
  resetDraft.value = '';
  resetModalOpen.value = true;
};

const confirmResetPassword = async () => {
  if (!resetTarget.value || !resetDraft.value.trim()) return;
  try {
    await resetUserPassword(resetTarget.value.id, resetDraft.value.trim());
    message.success(`已重置 ${resetTarget.value.username} 的密码`);
    resetModalOpen.value = false;
  } catch (error) {
    message.error((error as Error).message || '重置失败');
  }
};

const myPwdModalOpen = ref(false);
const myOldPwd = ref('');
const myNewPwd = ref('');

const openChangeMyPassword = () => {
  myOldPwd.value = '';
  myNewPwd.value = '';
  myPwdModalOpen.value = true;
};

const confirmChangeMyPassword = async () => {
  if (!myOldPwd.value || !myNewPwd.value) return;
  try {
    await changeMyPassword(myOldPwd.value, myNewPwd.value);
    message.success('密码已修改,下次登录请使用新密码');
    myPwdModalOpen.value = false;
  } catch (error) {
    message.error((error as Error).message || '修改失败');
  }
};

const EVENT_LABELS: Record<string, string> = {
  generate: '生成简历',
  chat: 'AI 对话',
  export_docx: '导出 Word',
  register: '注册',
  login: '登录',
  llm_config_update: '模型配置保存',
  llm_config_reset: '模型配置重置',
  user_disabled: '禁用用户',
  user_enabled: '启用用户',
  password_reset: '重置密码',
  password_change: '修改密码'
};

const eventLabel = (type: string) => EVENT_LABELS[type] ?? type;

const eventColor = (type: string) => {
  if (type === 'user_disabled' || type === 'password_reset' || type === 'llm_config_update' || type === 'llm_config_reset') return 'volcano';
  if (type === 'generate' || type === 'chat') return 'processing';
  return 'default';
};

const formatTime = (iso: string) => (iso ? iso.slice(0, 19).replace('T', ' ') : '');

onMounted(() => {
  loadStats();
  loadUsers();
  loadEvents();
});
</script>

<style scoped>
.admin-page {
  min-height: calc(100vh - 60px);
  padding: 24px;
  background: var(--stage-gradient);
}

.admin-shell {
  max-width: 1080px;
  margin: 0 auto;
  border-radius: 22px;
  border: 1px solid var(--border-color);
  background: var(--panel-gradient);
  box-shadow: var(--panel-shadow);
  padding: 22px 26px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.admin-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-color);
}

.admin-header p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--inset-bg-strong);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-card span {
  color: var(--text-muted);
  font-size: 12px;
}

.stat-card strong {
  color: var(--text-color);
  font-size: 22px;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.panel {
  padding: 16px;
  border-radius: 14px;
  background: var(--inset-bg);
  border: 1px solid var(--border-color);
}

.panel h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-color);
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 140px;
}

.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 4px;
}

.bar {
  width: 100%;
  max-width: 28px;
  border-radius: 4px 4px 0 0;
  background: var(--primary-color);
  opacity: 0.85;
}

.bar-label {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
}

.provider-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.provider-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--inset-bg-strong);
  overflow: hidden;
}

.provider-fill {
  height: 100%;
  border-radius: 4px;
  background: var(--primary-color);
}

.provider-count {
  min-width: 36px;
  text-align: right;
  color: var(--text-muted);
  font-size: 12px;
}

.mini-table {
  width: 100%;
  border-collapse: collapse;
}

.mini-table td {
  padding: 7px 4px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-color);
  font-size: 13px;
}

.mini-table .num {
  text-align: right;
  color: var(--text-muted);
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 14px;
}

@media (max-width: 900px) {
  .stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .panel-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .admin-page {
    padding: 12px;
  }

  .admin-shell {
    padding: 14px;
    border-radius: 14px;
  }
}
</style>
