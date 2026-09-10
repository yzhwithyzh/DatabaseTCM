<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="logo" aria-label="EB-TCM 首页">
        <Logo :size="38" />
        <span class="wordmark">
          <span class="logo-main">EB-TCM</span>
          <span class="logo-sub">中成药循证指南库</span>
        </span>
      </router-link>

      <div class="search-box" v-if="$route.name !== 'home'">
        <el-autocomplete v-model="kw" :fetch-suggestions="fetchSuggest" placeholder="检索中成药、疾病、证候或指南" clearable
          class="header-search" @select="onSelect" @keyup.enter="go">
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #default="{ item }">
            <span class="sug-type">{{ CTX[item.type] || "指南" }}</span>{{ item.term }} <span class="muted" v-if="item.n">({{ item.n }})</span>
          </template>
        </el-autocomplete>
      </div>

      <nav class="nav" aria-label="主导航">
        <router-link to="/search"><el-icon><Search /></el-icon>检索</router-link>
        <router-link to="/advanced"><el-icon><Operation /></el-icon>高级检索 / PICOS</router-link>
        <router-link to="/compare"><el-icon><DataAnalysis /></el-icon>推荐对比</router-link>
      </nav>
    </div>
  </header>

  <main class="app-main">
    <router-view :key="$route.fullPath" />
  </main>

  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-brand"><Logo :size="22" /><span>EB-TCM 中成药循证指南库</span></div>
      <div class="footer-note">数据来源于公开发表的中成药临床指南与专家共识，推荐意见由模型抽取并经原文校验，仅供专业人员参考。</div>
    </div>
  </footer>
</template>

<script setup>
import { suggest } from "@/api";
import { CTX } from "@/labels";
import Logo from "@/components/Logo.vue";
const router = useRouter(); const route = useRoute();
const kw = ref(route.query.q || "");
async function fetchSuggest(q, cb) { if (!q) return cb([]); cb(await suggest(q)); }
function onSelect(item) {
  if (item.type === "guideline") router.push(`/guideline/${item.id}`);
  else router.push(`/entity/${item.type}/${encodeURIComponent(item.term)}`);
}
function go() { if (kw.value) router.push({ path: "/search", query: { q: kw.value } }); }
</script>

<style scoped>
.app-header { position: sticky; top: 0; z-index: 100; background: rgba(255, 255, 255, 0.92); backdrop-filter: saturate(160%) blur(10px); border-bottom: 1px solid var(--c-border); }
.header-inner { max-width: 1400px; margin: 0 auto; display: flex; align-items: center; gap: 28px; height: 64px; padding: 0 20px; }
.logo { display: flex; align-items: center; gap: 11px; flex-shrink: 0; }
.wordmark { display: flex; flex-direction: column; line-height: 1.1; }
.logo-main { font-size: 21px; font-weight: 800; color: var(--c-primary); letter-spacing: 1.5px; font-family: var(--font-sans); }
.logo-sub { color: var(--c-text-2); font-size: 12px; letter-spacing: 1.5px; margin-top: 3px; font-family: var(--font-serif); }
.search-box { flex: 1; max-width: 520px; }
.nav { margin-left: auto; display: flex; gap: 6px; }
.nav a { display: inline-flex; align-items: center; gap: 6px; color: var(--c-text-2); font-size: 14.5px; font-weight: 500; padding: 8px 12px; border-radius: 8px; position: relative; transition: color 0.15s var(--ease), background 0.15s var(--ease); }
.nav a:hover { color: var(--c-primary); background: var(--c-primary-50); }
.nav a.router-link-active { color: var(--c-primary); font-weight: 600; }
.nav a.router-link-active::after { content: ""; position: absolute; left: 12px; right: 12px; bottom: -13px; height: 2px; border-radius: 2px; background: var(--c-accent); }
.nav .el-icon { font-size: 16px; }
.app-main { flex: 1; }
.footer { border-top: 1px solid var(--c-border); background: #fff; }
.footer-inner { max-width: 1400px; margin: 0 auto; padding: 22px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.footer-brand { display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--c-text-2); font-size: 13px; }
.footer-note { color: var(--c-text-3); font-size: 12.5px; }
@media (max-width: 900px) {
  .header-inner { gap: 12px; }
  .logo-sub, .nav a span { display: none; }
  .nav a { padding: 8px; }
}
</style>

<style>
/* el-autocomplete 不透传 scoped 属性，这里用全局样式 */
.header-search { width: 100%; }
.header-search .el-input__wrapper { border-radius: 999px; background: #f4f6fa; box-shadow: none; padding-left: 14px; transition: box-shadow 0.15s var(--ease), background 0.15s var(--ease); }
.header-search .el-input__wrapper:hover { background: #eef1f6; }
.header-search .el-input__wrapper.is-focus { background: #fff; box-shadow: 0 0 0 2px var(--c-primary-100); }
</style>
