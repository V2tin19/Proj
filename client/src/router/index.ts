import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { hasSession, hasSkippedAuth } from "@/utils/auth";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "resume",
    component: () => import("@/views/resume/index.vue"),
    meta: { title: "AI简历 - 简历制作" }
  },
  {
    path: "/template",
    name: "template",
    component: () => import("@/views/template/index.vue"),
    meta: { title: "AI简历 - 模板市场" }
  },
  {
    path: "/agent",
    name: "agent",
    component: () => import("@/views/agent/index.vue"),
    meta: { title: "AI简历 - 智能体工作台" }
  },
  {
    path: "/setting",
    name: "setting",
    component: () => import("@/views/setting/index.vue"),
    meta: { title: "AI简历 - 网站配置" }
  },
  {
    path: "/aiDeep",
    name: "aiDeep",
    component: () => import("@/views/aiDeep/index.vue"),
    meta: { title: "AI简历 - AI深度交流", keepAlive: true }
  },
  {
    path: "/auth",
    name: "auth",
    component: () => import("@/views/auth/index.vue"),
    meta: { title: "AI简历 - 注册/登录" }
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("../views/404.vue")
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// 路由守卫:未登录且未选择匿名模式时,引导到注册/登录页。
// (服务端 AUTH_MODE=optional 时可"先逛逛";required 模式下接口 401 会自动回到本页)
router.beforeEach((to) => {
  if (to.name === "auth") return true;
  if (hasSession() || hasSkippedAuth()) return true;
  return { name: "auth", query: to.fullPath !== "/" ? { redirect: to.fullPath } : {} };
});

router.afterEach((to) => {
  document.title = (to.meta?.title as string) || "AI简历";
});

export default router;
