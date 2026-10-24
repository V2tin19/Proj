<template>
  <header class="navbar">
    <nav>
      <ul>
        <li>
          <router-link to="/">
            <SvgIcon iconName="resume" />
            简历制作
          </router-link>
        </li>
        <li ref="templateStore">
          <router-link to="/template">
            <SvgIcon iconName="templateStore" />
            模板市场
          </router-link>
        </li>
        <li>
          <router-link to="/agent">
            <SvgIcon iconName="example" />
            简历智能体
          </router-link>
        </li>
        <li>
          <router-link to="/aiDeep">
            <SvgIcon iconName="ai" />
            AI深度交流
          </router-link>
        </li>
        <!-- 移动端底栏入口:打开账号与设置抽屉 -->
        <li class="mobile-only">
          <a role="button" tabindex="0" @click="drawerOpen = true" @keydown.enter="drawerOpen = true">
            <SvgIcon iconName="setting" />
            我的
          </a>
        </li>
      </ul>
    </nav>

    <!-- 桌面端右上角用户区 -->
    <div class="user-area">
      <a-dropdown :trigger="['click']">
        <button ref="userMenuRef" class="user-chip" type="button">
          <span class="user-avatar">{{ session ? session.username.slice(0, 1).toUpperCase() : '?' }}</span>
          <span class="user-name">{{ session ? session.username : '未登录' }}</span>
        </button>
        <template #overlay>
          <a-menu @click="onMenuClick">
            <a-menu-item key="settings">
              <setting-outlined />
              账号与设置
            </a-menu-item>
            <a-menu-item v-if="session" key="logout">
              <logout-outlined />
              退出登录
            </a-menu-item>
            <a-menu-item v-else key="auth">
              <user-outlined />
              注册 / 登录
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </header>

  <UserSettingsDrawer v-model:open="drawerOpen" />

  <a-tour
    v-model:open="tourOpen"
    :steps="tourSteps"
    :mask="true"
    :next-button-props="{ children: '下一步' }"
    :prev-button-props="{ children: '上一步' }"
    :finish-button-props="{ children: '完成' }"
    @finish="handleFinish"
    @close="handleFinish"
  />
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { TourProps } from "ant-design-vue";
import { SettingOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons-vue';
import SvgIcon from "../SvgIcon.vue";
import UserSettingsDrawer from "../UserSettingsDrawer.vue";
import { useResumeStore } from "../../store/useResumeStore";
import { getSessionUser, clearSession, type SessionUser } from "../../utils/auth";

const store = useResumeStore();
const route = useRoute();
const router = useRouter();
const templateStore = ref(null);
const userMenuRef = ref(null);
const tourOpen = ref(false);
const drawerOpen = ref(false);
// Header 常驻挂载,登录/退出后靠路由变化刷新显示
const session = ref<SessionUser | null>(getSessionUser());
watch(
  () => route.fullPath,
  () => {
    session.value = getSessionUser();
  }
);

const onMenuClick = ({ key }: { key: string | number }) => {
  if (key === 'settings') {
    drawerOpen.value = true;
  } else if (key === 'logout') {
    drawerOpen.value = true;
  } else if (key === 'auth') {
    clearSession();
    router.push({ name: 'auth' });
  }
};

const tourSteps: TourProps["steps"] = [
  {
    title: "账号与设置",
    description: "右上角账号入口可注册/登录账号;在账号与设置中可切换服务端地址与主题外观(支持跟随系统)。",
    target: () => userMenuRef.value,
  },
  {
    title: "选择模板",
    description: "然后进入模板市场，挑选适合自己的简历模板。",
    target: () => templateStore.value,
  }
];

const handleFinish = () => {
  tourOpen.value = false;
};

onMounted(() => {
  if (store.isFirstVisit) {
    tourOpen.value = true;
  }
});
</script>

<style scoped>
.navbar {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 4px 20px var(--shadow-color);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 72px;
  padding: 0 16px;
  transition: background 0.3s ease, border-color 0.3s ease;
}

:global(html.dark) .navbar {
  background: linear-gradient(90deg, rgba(4, 7, 13, 0.98), rgba(13, 20, 32, 0.96) 40%, rgba(15, 31, 61, 0.95) 100%);
  box-shadow: 0 16px 40px var(--shadow-color);
}

.navbar nav {
  width: min(100%, 880px);
}

.navbar nav ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.navbar nav ul li a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: var(--text-color);
  text-align: center;
  font-size: 16px;
  min-height: 44px;
  padding: 0 14px;
  text-decoration: none;
  transition: all 0.22s;
  border-radius: 12px;
  white-space: nowrap;
  cursor: pointer;
}

.navbar nav ul li a:hover {
  background-color: rgba(45, 91, 255, 0.1);
  color: var(--primary-color);
}

.navbar nav ul li .router-link-active {
  background: rgba(45, 91, 255, 0.16);
  color: var(--primary-color);
  font-weight: 600;
}

:global(html.dark) .navbar nav ul li a:hover {
  background-color: rgba(59, 108, 255, 0.18);
  color: #ffffff;
}

:global(html.dark) .navbar nav ul li .router-link-active {
  background: rgba(59, 108, 255, 0.24);
  color: #ffffff;
}

.navbar :deep(.svg-icon) {
  font-size: 18px;
}

/* 桌面端用户区 */
.user-area {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 4px 12px 4px 4px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--bg-card-color);
  color: var(--text-color);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-chip:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: #ffffff;
  font-weight: 600;
  font-size: 14px;
}

.user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-only {
  display: none;
}

@media (max-width: 768px) {
  .navbar {
    position: fixed;
    inset: auto 0 0 0;
    min-height: calc(64px + env(safe-area-inset-bottom));
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
    border-top: 1px solid var(--border-color);
    border-bottom: 0;
    box-shadow: 0 -14px 32px var(--shadow-color);
  }

  .navbar nav {
    width: 100%;
  }

  .navbar nav ul {
    justify-content: space-between;
    gap: 2px;
  }

  .navbar nav ul li {
    flex: 1;
    min-width: 0;
  }

  .navbar nav ul li a {
    width: 100%;
    min-height: 52px;
    padding: 6px 2px;
    flex-direction: column;
    gap: 4px;
    border-radius: 12px;
    font-size: 11px;
    line-height: 1.15;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .navbar :deep(.svg-icon) {
    font-size: 20px;
  }

  .user-area {
    display: none;
  }

  .mobile-only {
    display: list-item;
  }
}
</style>
