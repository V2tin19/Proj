import { createApp } from 'vue';
import { createPinia } from 'pinia';
import Antd from 'ant-design-vue';
import App from './App.vue';
import 'ant-design-vue/dist/reset.css';
// Font Awesome(简历模板 C/D 的联系方式/分区图标)
import '@fortawesome/fontawesome-free/css/all.min.css';
import 'virtual:svg-icons-register';
import router from './router'; // 引入路由
// 引入全局主题颜色
import './assets/styles/theme.css';
import './assets/styles/dark.css';
// 持久化pinia
import piniaPersist from 'pinia-plugin-persistedstate'
import lazyLoad from './directives/lazyLoad';
import { isTauriEnv, setAutoServerBase } from './utils/auth';

async function bootstrap() {
  // Tauri 桌面端:先向壳要后端地址(壳已在 setup 阶段拉起/探测好后端),
  // 再挂载应用,保证首个 API 请求就拿到正确地址
  if (isTauriEnv()) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const info = await invoke<{ url: string; managed: boolean }>('backend_info');
      if (info?.url) {
        setAutoServerBase(info.url);
      }
    } catch (e) {
      console.warn('backend_info 获取失败,回退默认服务端地址', e);
    }
  }

  const pinia = createPinia()
  pinia.use(piniaPersist) // 启用持久化功能

  const app = createApp(App);
  app.use(router);
  app.use(pinia);
  app.directive('lazy', lazyLoad);
  app.use(Antd);
  app.mount('#app');
}

void bootstrap();
