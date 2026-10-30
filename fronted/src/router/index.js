import { createRouter, createWebHistory } from "vue-router";
import { auth, clearLogin } from "@/auth";
import { getMemberInfo } from "@/api";

const routes = [
  { path: "/login", name: "login", component: () => import("@/views/Login.vue"), meta: { public: true, title: "登录" } },
  { path: "/", name: "home", component: () => import("@/views/Home.vue") },
  { path: "/search", name: "search", component: () => import("@/views/Search.vue") },
  { path: "/advanced", name: "advanced", component: () => import("@/views/Advanced.vue") },
  { path: "/guideline/:id", name: "guideline", component: () => import("@/views/Guideline.vue") },
  { path: "/entity/:type/:term", name: "entity", component: () => import("@/views/Entity.vue") },
  { path: "/compare", name: "compare", component: () => import("@/views/Compare.vue") },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

// 除登录页外全部需要登录
router.beforeEach(async (to) => {
  if (to.meta.public) {
    return to.name === "login" && auth.token ? { path: to.query.redirect || "/" } : true;
  }
  if (!auth.token) return { name: "login", query: to.fullPath === "/" ? {} : { redirect: to.fullPath } };
  if (!auth.member) {
    try {
      auth.member = await getMemberInfo();
    } catch {
      clearLogin();
      return { name: "login", query: { redirect: to.fullPath } };
    }
  }
  return true;
});

export default router;
