import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';

export type ThemeMode = 'light' | 'dark' | 'system';

export const useSettingsStore = defineStore('settings', () => {
  const getStoredMode = (): ThemeMode => {
    const val = localStorage.getItem('themeMode');
    if (val === 'light' || val === 'dark' || val === 'system') {
      return val;
    }
    // 兼容存量 'theme' 键名
    const legacy = localStorage.getItem('theme');
    if (legacy === 'light' || legacy === 'dark') {
      return legacy;
    }
    return 'system';
  };

  const themeMode = ref<ThemeMode>(getStoredMode());
  const systemPrefersDark = ref<boolean>(
    typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false
  );

  const isDark = computed<boolean>(() => {
    if (themeMode.value === 'dark') return true;
    if (themeMode.value === 'light') return false;
    return systemPrefersDark.value;
  });

  const theme = computed<string>(() => (isDark.value ? '#3b6cff' : '#2d5bff'));

  const applyDomTheme = (dark: boolean) => {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', dark);
    }
  };

  const setThemeMode = (mode: ThemeMode) => {
    themeMode.value = mode;
    localStorage.setItem('themeMode', mode);
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
    applyDomTheme(isDark.value);
  };

  // 快捷切换
  const toggleTheme = () => {
    if (themeMode.value === 'dark') {
      setThemeMode('light');
    } else {
      setThemeMode('dark');
    }
  };

  let mediaQueryListenerAttached = false;
  const initTheme = () => {
    // 绑定系统明暗模式监听
    if (typeof window !== 'undefined' && window.matchMedia && !mediaQueryListenerAttached) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      systemPrefersDark.value = mediaQuery.matches;

      const onChange = (e: MediaQueryListEvent) => {
        systemPrefersDark.value = e.matches;
        if (themeMode.value === 'system') {
          applyDomTheme(e.matches);
        }
      };

      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', onChange);
      } else if ('addListener' in mediaQuery) {
        (mediaQuery as { addListener: (cb: (e: MediaQueryListEvent) => void) => void }).addListener(onChange);
      }
      mediaQueryListenerAttached = true;
    }

    applyDomTheme(isDark.value);
  };

  watch(isDark, (val) => {
    applyDomTheme(val);
  });

  return {
    themeMode,
    isDark,
    theme,
    setThemeMode,
    toggleTheme,
    initTheme,
  };
});
