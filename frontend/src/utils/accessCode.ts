/**
 * 访问口令(X-Access-Code)存取。
 * 后端 .env 设置 ACCESS_CODE 后,所有业务接口需要该请求头;
 * 前端在「网站配置」页填一次,存于 localStorage。
 * 独立成模块避免 store 与 api 层的循环依赖。
 */

const STORAGE_KEY = "accessCode";

export function getAccessCode(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setAccessCode(code: string): void {
  try {
    if (code) {
      localStorage.setItem(STORAGE_KEY, code);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    /* localStorage 不可用时静默 */
  }
}
