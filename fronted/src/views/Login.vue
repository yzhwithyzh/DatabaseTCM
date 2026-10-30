<template>
  <div class="login-page">
    <section class="brand">
      <div class="brand-inner">
        <div class="brand-logo">
          <Logo :size="52" />
          <div>
            <div class="brand-name">EB-TCM</div>
            <div class="brand-sub">中医药循证指南库</div>
          </div>
        </div>
        <h1 class="brand-title">让每一条推荐意见<br />都能回到原文与证据</h1>
        <ul class="brand-points">
          <li><el-icon><Collection /></el-icon>汇集中医药临床指南、专家共识与团体标准</li>
          <li><el-icon><Filter /></el-icon>按疾病、证候、中成药与 PICOS 精准检索</li>
          <li><el-icon><DataAnalysis /></el-icon>跨指南对比推荐强度与证据等级</li>
        </ul>
        <p class="brand-note">本库面向授权用户开放，请使用管理员分配的账号登录，或提交账号申请。</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel-card">
        <!-- 注册提交成功 -->
        <template v-if="submitted">
          <el-result icon="success" title="申请已提交" sub-title="管理员审核通过后即可使用该账号登录，请耐心等待。">
            <template #extra><el-button type="primary" @click="backToLogin">返回登录</el-button></template>
          </el-result>
        </template>

        <template v-else>
          <div class="tabs" role="tablist">
            <button type="button" role="tab" :class="{ on: mode === 'login' }" :aria-selected="mode === 'login'" @click="switchMode('login')">账号登录</button>
            <button type="button" role="tab" :class="{ on: mode === 'register' }" :aria-selected="mode === 'register'" @click="switchMode('register')">申请账号</button>
          </div>

          <!-- 登录 -->
          <el-form v-if="mode === 'login'" ref="loginRef" :model="lf" :rules="loginRules" size="large" @submit.prevent="doLogin">
            <el-form-item prop="userName">
              <el-input v-model="lf.userName" placeholder="用户名" autocomplete="username" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="lf.password" type="password" show-password placeholder="密码" autocomplete="current-password" prefix-icon="Lock" />
            </el-form-item>
            <el-form-item prop="code">
              <div class="captcha-row">
                <el-input v-model="lf.code" placeholder="验证码" prefix-icon="Key" @keyup.enter="doLogin" />
                <img :src="captcha.img" class="captcha" alt="验证码，点击刷新" title="点击刷新" @click="loadCaptcha" />
              </div>
            </el-form-item>
            <el-button type="primary" native-type="submit" class="submit" :loading="busy">登 录</el-button>
            <p class="hint">还没有账号？<a href="#" @click.prevent="switchMode('register')">提交申请</a>，审核通过后即可登录。忘记密码请联系管理员重置。</p>
          </el-form>

          <!-- 注册申请 -->
          <el-form v-else ref="regRef" :model="rf" :rules="regRules" label-position="top" class="reg-form" @submit.prevent="doRegister">
            <div class="grid">
              <el-form-item label="用户名" prop="userName"><el-input v-model="rf.userName" placeholder="4-50 位字母、数字" autocomplete="username" /></el-form-item>
              <el-form-item label="姓名" prop="realName"><el-input v-model="rf.realName" /></el-form-item>
              <el-form-item label="密码" prop="password"><el-input v-model="rf.password" type="password" show-password placeholder="8 位以上，含字母和数字" autocomplete="new-password" /></el-form-item>
              <el-form-item label="确认密码" prop="password2"><el-input v-model="rf.password2" type="password" show-password autocomplete="new-password" /></el-form-item>
              <el-form-item label="单位" prop="organization"><el-input v-model="rf.organization" placeholder="如 南京中医药大学" /></el-form-item>
              <el-form-item label="部门 / 科室"><el-input v-model="rf.department" /></el-form-item>
              <el-form-item label="职称 / 身份"><el-input v-model="rf.jobTitle" placeholder="如 主治医师、研究生" /></el-form-item>
              <el-form-item label="手机" prop="phone"><el-input v-model="rf.phone" /></el-form-item>
            </div>
            <el-form-item label="邮箱" prop="email"><el-input v-model="rf.email" /></el-form-item>
            <el-form-item label="申请用途"><el-input v-model="rf.applyReason" type="textarea" :rows="2" maxlength="500" placeholder="选填，便于管理员审核，如：临床决策参考、课题研究" /></el-form-item>
            <el-form-item label="验证码" prop="code">
              <div class="captcha-row">
                <el-input v-model="rf.code" />
                <img :src="captcha.img" class="captcha" alt="验证码，点击刷新" title="点击刷新" @click="loadCaptcha" />
              </div>
            </el-form-item>
            <el-button type="primary" native-type="submit" class="submit" size="large" :loading="busy">提交申请</el-button>
            <p class="hint">已有账号？<a href="#" @click.prevent="switchMode('login')">直接登录</a></p>
          </el-form>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { getCaptcha, login, register } from "@/api";
import { setLogin } from "@/auth";
import Logo from "@/components/Logo.vue";

const route = useRoute(); const router = useRouter();
const mode = ref("login"); const busy = ref(false); const submitted = ref(false);
const captcha = reactive({ img: "", uuid: "" });
const loginRef = ref(); const regRef = ref();
const lf = reactive({ userName: "", password: "", code: "" });
const rf = reactive({ userName: "", password: "", password2: "", realName: "", organization: "", department: "", jobTitle: "", phone: "", email: "", applyReason: "", code: "" });

const req = (msg) => ({ required: true, message: msg, trigger: "blur" });
const loginRules = { userName: [req("请输入用户名")], password: [req("请输入密码")], code: [req("请输入验证码")] };
const regRules = {
  userName: [req("请输入用户名"), { pattern: /^[A-Za-z0-9_@.\-]{4,50}$/, message: "4-50 位字母、数字或 _ @ . -", trigger: "blur" }],
  realName: [req("请输入姓名")],
  password: [req("请输入密码"), { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, message: "8-32 位，且同时包含字母和数字", trigger: "blur" }],
  password2: [req("请再次输入密码"), { validator: (_, v, cb) => cb(v === rf.password ? undefined : new Error("两次输入的密码不一致")), trigger: "blur" }],
  organization: [req("请输入单位")],
  phone: [{ pattern: /^[\d\-+ ]{6,20}$/, message: "手机号格式不正确", trigger: "blur" }],
  email: [{ type: "email", message: "邮箱格式不正确", trigger: "blur" }],
  code: [req("请输入验证码")],
};

async function loadCaptcha() {
  const d = await getCaptcha();
  captcha.img = "data:image/gif;base64," + d.img; captcha.uuid = d.uuid;
}
function switchMode(m) { mode.value = m; lf.code = ""; rf.code = ""; loadCaptcha(); }
function backToLogin() { submitted.value = false; lf.userName = rf.userName; switchMode("login"); }

async function doLogin() {
  if (!(await loginRef.value.validate().catch(() => false))) return;
  busy.value = true;
  try {
    const d = await login({ userName: lf.userName.trim(), password: lf.password, code: lf.code, uuid: captcha.uuid });
    setLogin(d.token, d.member);
    router.replace(route.query.redirect || "/");
  } catch {
    lf.code = ""; loadCaptcha();
  } finally { busy.value = false; }
}

async function doRegister() {
  if (!(await regRef.value.validate().catch(() => false))) return;
  busy.value = true;
  try {
    const { password2, ...data } = rf;
    await register({ ...data, userName: rf.userName.trim(), uuid: captcha.uuid });
    submitted.value = true;
  } catch {
    rf.code = ""; loadCaptcha();
  } finally { busy.value = false; }
}

loadCaptcha();
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); background: var(--c-bg); }

.brand { position: relative; overflow: hidden; color: #fff; background: radial-gradient(120% 90% at 0% 0%, #2a6094 0%, var(--c-primary) 45%, #12304b 100%); display: flex; align-items: center; justify-content: center; padding: 48px; }
.brand::after { content: ""; position: absolute; right: -120px; bottom: -120px; width: 420px; height: 420px; border-radius: 50%; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 0 0 60px rgba(255, 255, 255, 0.025), 0 0 0 120px rgba(255, 255, 255, 0.02); }
.brand-inner { position: relative; z-index: 1; max-width: 460px; }
.brand-logo { display: flex; align-items: center; gap: 14px; }
.brand-name { font-size: 26px; font-weight: 800; letter-spacing: 2px; }
.brand-sub { font-family: var(--font-serif); font-size: 14px; letter-spacing: 2px; opacity: 0.85; margin-top: 2px; }
.brand-title { color: #fff; font-family: var(--font-serif); font-size: 30px; line-height: 1.5; font-weight: 700; letter-spacing: 1px; margin: 48px 0 28px; }
.brand-points { list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }
.brand-points li { display: flex; align-items: center; gap: 10px; font-size: 15px; opacity: 0.92; }
.brand-points .el-icon { color: #f0c86a; font-size: 18px; flex-shrink: 0; }
.brand-note { margin: 40px 0 0; padding-top: 18px; border-top: 1px solid rgba(255, 255, 255, 0.15); font-size: 13px; line-height: 1.7; opacity: 0.7; }

.panel { display: flex; align-items: center; justify-content: center; padding: 40px 24px; }
.panel-card { width: 100%; max-width: 440px; background: var(--c-card); border: 1px solid var(--c-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-md); padding: 28px 32px 22px; }
.tabs { display: flex; gap: 24px; border-bottom: 1px solid var(--c-border); margin-bottom: 24px; }
.tabs button { position: relative; background: none; border: 0; padding: 0 0 12px; font: inherit; font-size: 17px; font-weight: 600; color: var(--c-text-3); cursor: pointer; transition: color 0.15s var(--ease); }
.tabs button:hover { color: var(--c-text-2); }
.tabs button.on { color: var(--c-primary); }
.tabs button.on::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px; border-radius: 2px; background: var(--c-accent); }

.captcha-row { display: flex; gap: 10px; width: 100%; }
.captcha-row .el-input { flex: 1; }
.captcha { height: 40px; width: 110px; border-radius: var(--radius-sm); border: 1px solid var(--c-border); cursor: pointer; object-fit: cover; background: #f4f6fa; }
.reg-form .captcha { height: 32px; }
.submit { width: 100%; margin-top: 4px; }
.hint { margin: 16px 0 0; text-align: center; color: var(--c-text-3); font-size: 13px; line-height: 1.7; }

.reg-form .grid { display: grid; grid-template-columns: 1fr 1fr; column-gap: 14px; }
.reg-form :deep(.el-form-item) { margin-bottom: 14px; }
.reg-form :deep(.el-form-item__label) { padding-bottom: 2px; font-size: 13px; }
.panel-card:has(.reg-form) { max-width: 520px; }

@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .brand { padding: 32px 24px; }
  .brand-title, .brand-points, .brand-note { display: none; }
  .reg-form .grid { grid-template-columns: 1fr; }
}
</style>
