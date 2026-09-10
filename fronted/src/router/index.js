import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", name: "home", component: () => import("@/views/Home.vue") },
  { path: "/search", name: "search", component: () => import("@/views/Search.vue") },
  { path: "/advanced", name: "advanced", component: () => import("@/views/Advanced.vue") },
  { path: "/guideline/:id", name: "guideline", component: () => import("@/views/Guideline.vue") },
  { path: "/entity/:type/:term", name: "entity", component: () => import("@/views/Entity.vue") },
  { path: "/compare", name: "compare", component: () => import("@/views/Compare.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});
