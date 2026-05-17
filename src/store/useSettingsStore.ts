import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useSettingsStore = defineStore(
  'settings',
  () => {
    const getStoredTheme = () => localStorage.getItem('theme');
    const isDark = ref<boolean>(getStoredTheme() ? getStoredTheme() === 'dark' : true);
    const theme = ref<string>(isDark.value ? '#3b6cff' : '#2d5bff');
    const aliApiKey = ref<string>('');
    const aliApiUrl = import.meta.env.VITE_API_URL;
    const modelName = ref<string>('qwen-turbo');

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
      toggleTheme,
      initTheme,
      aliApiKey,
      aliApiUrl,
      modelName
    };
  },
  {
    persist: true,
  }
);
