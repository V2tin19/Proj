<template>
  <div class="auth-container">
    <a-card class="auth-card" :bordered="false">
      <h2 class="title">AI 简历生成器</h2>
      <p class="subtitle">注册账号即可使用,数据与账号绑定</p>

      <!-- 服务端地址(首次使用引导) -->
      <div class="server-row">
        <a-input
          v-model:value="serverUrl"
          placeholder="服务端地址,如 http://192.168.1.10:8000(同源部署可留空)"
          allow-clear
        />
      </div>

      <a-tabs v-model:activeKey="mode" centered>
        <!-- 登录 -->
        <a-tab-pane key="login" tab="登录">
          <a-form layout="vertical" @submit.prevent>
            <a-form-item label="用户名">
              <a-input v-model:value="loginForm.username" placeholder="用户名" allow-clear @pressEnter="submitLogin" />
            </a-form-item>
            <a-form-item label="密码">
              <a-input-password v-model:value="loginForm.password" placeholder="密码" @pressEnter="submitLogin" />
            </a-form-item>
            <a-button type="primary" block :loading="busy" @click="submitLogin">登录</a-button>
          </a-form>
        </a-tab-pane>

        <!-- 注册 -->
        <a-tab-pane key="register" tab="注册新账号">
          <a-form layout="vertical" @submit.prevent>
            <a-form-item label="用户名(4-32 位字母/数字/_/-)">
              <a-input v-model:value="registerForm.username" placeholder="用户名" allow-clear />
            </a-form-item>
            <a-form-item label="密码(≥8 位,含字母和数字)">
              <a-input-password v-model:value="registerForm.password" placeholder="密码" />
            </a-form-item>
            <a-form-item label="确认密码">
              <a-input-password v-model:value="registerForm.confirm" placeholder="再次输入密码" />
            </a-form-item>
            <a-form-item label="邮箱(选填,用于后续账号找回)">
              <a-input v-model:value="registerForm.email" placeholder="email@example.com" allow-clear />
            </a-form-item>
            <a-form-item v-if="needInviteCode" label="邀请码">
              <a-input v-model:value="registerForm.inviteCode" placeholder="邀请码" allow-clear />
            </a-form-item>
            <a-button type="primary" block :loading="busy" @click="submitRegister">注册并登录</a-button>
          </a-form>
        </a-tab-pane>
      </a-tabs>

      <div class="skip-row">
        <a @click="skip">先逛逛(匿名模式,功能可能受限)</a>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { message } from "ant-design-vue";
import { loginAccount, registerAccount, type SessionPayload } from "../../api/agentAPI";
import { getServerBase, markAuthSkipped, saveSession, setServerBase } from "../../utils/auth";

const route = useRoute();
const router = useRouter();

const mode = ref<"login" | "register">("login");
const busy = ref(false);
const serverUrl = ref<string>(getServerBase());
const needInviteCode = ref(false); // 服务端 invite 模式由 403 提示触发,不预知配置

const loginForm = reactive({ username: "", password: "" });
const registerForm = reactive({ username: "", password: "", confirm: "", email: "", inviteCode: "" });

const applySession = (payload: SessionPayload) => {
  if (serverUrl.value.trim() !== getServerBase()) {
    setServerBase(serverUrl.value);
  }
  saveSession(payload.token, { username: payload.username, role: payload.role });
  const redirect = (route.query.redirect as string) || "/";
  router.push(redirect);
};

const submitLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    message.warning("请输入用户名和密码");
    return;
  }
  busy.value = true;
  try {
    setServerBase(serverUrl.value);
    const payload = await loginAccount({ ...loginForm });
    message.success(`欢迎回来,${payload.username}`);
    applySession(payload);
  } catch (error) {
    message.error((error as Error).message || "登录失败");
  } finally {
    busy.value = false;
  }
};

const submitRegister = async () => {
  const { username, password, confirm, email, inviteCode } = registerForm;
  if (!/^[A-Za-z0-9_-]{4,32}$/.test(username)) {
    message.warning("用户名须为 4-32 位字母、数字、下划线或连字符");
    return;
  }
  if (password.length < 8 || !/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    message.warning("密码至少 8 位,且须同时包含字母和数字");
    return;
  }
  if (password !== confirm) {
    message.warning("两次输入的密码不一致");
    return;
  }
  busy.value = true;
  try {
    setServerBase(serverUrl.value);
    const payload = await registerAccount({ username, password, email, inviteCode });
    message.success("注册成功,已自动登录");
    applySession(payload);
  } catch (error) {
    const err = error as Error & { code?: number };
    if (err.code === 403) {
      needInviteCode.value = true;
      message.warning("当前注册需要邀请码,请填写后重试");
    } else {
      message.error(err.message || "注册失败");
    }
  } finally {
    busy.value = false;
  }
};

const skip = () => {
  setServerBase(serverUrl.value);
  markAuthSkipped();
  router.push((route.query.redirect as string) || "/");
};
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: var(--bg-color);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: linear-gradient(180deg, rgba(16, 23, 34, 0.96), rgba(10, 17, 27, 0.98));
  border-radius: 18px;
  border: 1px solid var(--border-color);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
  padding: 28px 24px;
}

.title {
  text-align: center;
  color: var(--primary-color);
  margin: 0 0 6px;
}

.subtitle {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  margin: 0 0 16px;
}

.server-row {
  margin-bottom: 12px;
}

.skip-row {
  text-align: center;
  margin-top: 14px;
  font-size: 12px;
}

.skip-row a {
  color: var(--text-muted);
}
</style>
