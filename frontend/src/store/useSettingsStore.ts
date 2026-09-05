import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { getAccessCode, setAccessCode } from '../utils/accessCode';

export const useSettingsStore = defineStore(
  'settings',
  () => {
    const getStoredTheme = () => localStorage.getItem('theme');
    const isDark = ref<boolean>(getStoredTheme() ? getStoredTheme() === 'dark' : true);
    const theme = ref<string>(isDark.value ? '#3b6cff' : '#2d5bff');

    // 访问口令(后端 .env 设置 ACCESS_CODE 后必填),真实来源是 localStorage
    const accessCode = ref<string>(getAccessCode());
    const updateAccessCode = (code: string) => {
      accessCode.value = code.trim();
      setAccessCode(accessCode.value);
    };

    const applyTheme = (dark: boolean) => {
      theme.value = dark ? '#3b6cff' : '#2d5bff';
      document.documentElement.classList.toggle('dark', dark);
    };

    const toggleTheme = () => {
      isDark.value = !isDark.value;
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
      applyTheme(isDark.value);
    };

    const initTheme = () => {
      const storedTheme = getStoredTheme();
      isDark.value = storedTheme ? storedTheme === 'dark' : true;
      if (!storedTheme) {
        localStorage.setItem('theme', 'dark');
      }
      applyTheme(isDark.value);
    };

    watch(isDark, (value) => {
      applyTheme(value);
    });

    return {
      isDark,
      theme,
      accessCode,
      updateAccessCode,
      toggleTheme,
      initTheme,
    };
  },
  {
    persist: true,
  }
);
