<template>
  <router-view v-if="$route.meta.public" />
  <template v-else>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="logo" aria-label="EB-TCM 首页">
        <Logo :size="38" />
        <span class="wordmark">
          <span class="logo-main">EB-TCM</span>
          <span class="logo-sub">中医药循证指南库</span>
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

      <el-dropdown v-if="auth.member" trigger="click" @command="onUserCmd">
        <button type="button" class="user-btn" aria-label="账号菜单">
          <span class="avatar">{{ auth.member.realName?.slice(-2) || "我" }}</span>
          <span class="user-name">{{ auth.member.realName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <div class="user-card">
            <div class="user-card-name">{{ auth.member.realName }}<span class="muted">（{{ auth.member.userName }}）</span></div>
            <div class="muted" v-if="auth.member.organization">{{ [auth.member.organization, auth.member.department].filter(Boolean).join(" · ") }}</div>
            <div class="muted">账号有效期：{{ auth.member.expireDate || "长期" }}</div>
          </div>
          <el-dropdown-menu>
            <el-dropdown-item command="pwd" icon="Key">修改密码</el-dropdown-item>
            <el-dropdown-item command="logout" icon="SwitchButton" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>

  <main class="app-main">
    <router-view :key="$route.fullPath" />
  </main>

  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-brand"><Logo :size="22" /><span>EB-TCM 中医药循证指南库</span></div>
      <div class="footer-note">数据来源于公开发表的中医药临床指南与专家共识，推荐意见由模型抽取并经原文校验，仅供专业人员参考。</div>
    </div>
  </footer>

  <el-dialog v-model="pwdOpen" title="修改密码" width="420px" append-to-body @closed="pwdRef?.resetFields()">
    <el-form ref="pwdRef" :model="pwd" :rules="pwdRules" label-width="80px" @submit.prevent="savePwd">
      <el-form-item label="原密码" prop="oldPassword"><el-input v-model="pwd.oldPassword" type="password" show-password autocomplete="current-password" /></el-form-item>
      <el-form-item label="新密码" prop="newPassword"><el-input v-model="pwd.newPassword" type="password" show-password placeholder="8 位以上，含字母和数字" autocomplete="new-password" /></el-form-item>
      <el-form-item label="确认密码" prop="confirm"><el-input v-model="pwd.confirm" type="password" show-password autocomplete="new-password" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdOpen = false">取消</el-button>
      <el-button type="primary" :loading="pwdBusy" @click="savePwd">保存</el-button>
    </template>
  </el-dialog>
  </template>
</template>

<script setup>
import { ElMessage, ElMessageBox } from "element-plus";
import { suggest, logout, changePassword } from "@/api";
import { auth, clearLogin } from "@/auth";
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

// ---------- 账号 ----------
const pwdOpen = ref(false); const pwdBusy = ref(false); const pwdRef = ref();
const pwd = reactive({ oldPassword: "", newPassword: "", confirm: "" });
const pwdRules = {
  oldPassword: [{ required: true, message: "请输入原密码", trigger: "blur" }],
  newPassword: [{ required: true, message: "请输入新密码", trigger: "blur" }, { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, message: "8-32 位，且同时包含字母和数字", trigger: "blur" }],
  confirm: [{ validator: (_, v, cb) => cb(v === pwd.newPassword ? undefined : new Error("两次输入的密码不一致")), trigger: "blur" }],
};
async function savePwd() {
  if (!(await pwdRef.value.validate().catch(() => false))) return;
  pwdBusy.value = true;
  try {
    await changePassword({ oldPassword: pwd.oldPassword, newPassword: pwd.newPassword });
    ElMessage.success("密码已修改"); pwdOpen.value = false;
  } finally { pwdBusy.value = false; }
}
async function onUserCmd(cmd) {
  if (cmd === "pwd") { pwdOpen.value = true; return; }
  await ElMessageBox.confirm("确定退出登录？", "提示", { type: "warning" });
  await logout().catch(() => {});
  clearLogin();
  router.replace({ name: "login" });
}
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
.user-btn { display: inline-flex; align-items: center; gap: 8px; background: none; border: 0; padding: 4px 6px 4px 4px; border-radius: 999px; cursor: pointer; color: var(--c-text-2); font: inherit; font-size: 14px; transition: background 0.15s var(--ease); }
.user-btn:hover { background: var(--c-primary-50); }
.avatar { width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: var(--c-primary); color: #fff; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; }
.user-name { max-width: 6em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-card { padding: 10px 16px 8px; min-width: 220px; border-bottom: 1px solid var(--c-border); line-height: 1.7; }
.user-card-name { font-weight: 600; color: var(--c-text); }
.app-main { flex: 1; }
.footer { border-top: 1px solid var(--c-border); background: #fff; }
.footer-inner { max-width: 1400px; margin: 0 auto; padding: 22px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.footer-brand { display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--c-text-2); font-size: 13px; }
.footer-note { color: var(--c-text-3); font-size: 12.5px; }
@media (max-width: 900px) {
  .header-inner { gap: 12px; }
  .logo-sub, .nav a span, .user-name { display: none; }
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
