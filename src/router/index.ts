import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

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
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("../views/404.vue")
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

router.afterEach((to) => {
  document.title = (to.meta?.title as string) || "AI简历";
});

export default router;
