import { ref } from 'vue';
import { getBackendHealth } from '../api/agentAPI';

/**
 * 后端连接状态(模块级单例):启动探测 + 30s 轮询 + 窗口聚焦/可见性复检。
 * 离线时仅降级 AI 类功能,编辑与本地导出不受影响。
 */
export type BackendStatus = 'unknown' | 'ok' | 'down';

export interface BackendHealthInfo {
  ok: boolean;
  now: string;
  provider: string;
}

const status = ref<BackendStatus>('unknown');
const info = ref<BackendHealthInfo | null>(null);
let started = false;
let probing = false;
let timer: ReturnType<typeof setInterval> | undefined;

async function probe() {
  if (probing) return;
  probing = true;
  try {
    info.value = await getBackendHealth();
    status.value = 'ok';
  } catch {
    info.value = null;
    status.value = 'down';
  } finally {
    probing = false;
  }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    probe();
  }
}

export function useBackendHealth() {
  const start = () => {
    if (started || typeof window === 'undefined') return;
    started = true;
    probe();
    timer = setInterval(probe, 30_000);
    window.addEventListener('focus', probe);
    document.addEventListener('visibilitychange', onVisibilityChange);
  };

  const stop = () => {
    if (timer !== undefined) clearInterval(timer);
    window.removeEventListener('focus', probe);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    started = false;
  };

  return { status, info, refresh: probe, start, stop };
}
