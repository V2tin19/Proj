/**
 * 登录会话与服务端地址的存取(单一数据源,供 store / api / worker 共用)。
 * 令牌为 C/S 模式凭证;服务端地址留空 = 同源(web 模式与开发代理)。
 */

const TOKEN_KEY = "auth.token";
const USER_KEY = "auth.user"; // JSON: {username, role, email}
const SERVER_URL_KEY = "server.url";
const SKIPPED_KEY = "auth.skipped"; // 匿名模式(迁移期 AUTH_MODE=optional)记住跳过

export interface SessionUser {
  username: string;
  role: "user" | "admin";
  email?: string;
}

function safeGet(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function safeSet(key: string, value: string): void {
  try {
    if (value) {
      localStorage.setItem(key, value);
    } else {
      localStorage.removeItem(key);
    }
  } catch {
    /* storage 不可用时静默 */
  }
}

// ---------------------------------------------------------------- 会话

export function getToken(): string {
  return safeGet(TOKEN_KEY);
}

export function getSessionUser(): SessionUser | null {
  const raw = safeGet(USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as SessionUser;
    return parsed?.username ? parsed : null;
  } catch {
    return null;
  }
}

export function saveSession(token: string, user: SessionUser): void {
  safeSet(TOKEN_KEY, token);
  safeSet(USER_KEY, JSON.stringify(user));
  safeSet(SKIPPED_KEY, ""); // 登录即清除匿名标记
}

export function clearSession(): void {
  safeSet(TOKEN_KEY, "");
  safeSet(USER_KEY, "");
}

export function hasSession(): boolean {
  return Boolean(getToken() && getSessionUser());
}

// ------------------------------------------------------------ 匿名模式

export function hasSkippedAuth(): boolean {
  return safeGet(SKIPPED_KEY) === "1";
}

export function markAuthSkipped(): void {
  safeSet(SKIPPED_KEY, "1");
}

// ---------------------------------------------------------- 服务端地址

export function getServerBase(): string {
  // 去除尾部斜杠,便于拼接 `${base}/api/...`
  return safeGet(SERVER_URL_KEY).replace(/\/+$/, "");
}

export function setServerBase(url: string): void {
  safeSet(SERVER_URL_KEY, url.trim());
}
