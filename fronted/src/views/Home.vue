<template>
  <section class="hero">
    <div class="hero-inner">
      <div class="hero-eyebrow"><Logo :size="30" /><span>Evidence-Based Chinese Patent Medicine Guidelines</span></div>
      <h1 class="hero-title">中成药循证指南库</h1>
      <p class="hero-sub">汇集公开发表的中成药临床指南与专家共识，每条推荐意见均可溯源至原文页码</p>
      <div class="hero-search-row">
        <el-autocomplete v-model="kw" :fetch-suggestions="fetchSuggest" placeholder="输入中成药、疾病、证候或指南名" clearable
          class="hero-search" size="large" @select="onSelect" @keyup.enter="go">
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #default="{ item }"><span class="sug-type">{{ CTX[item.type] || "指南" }}</span>{{ item.term }} <span class="muted" v-if="item.n">({{ item.n }})</span></template>
        </el-autocomplete>
        <button class="hero-btn" type="button" @click="go"><el-icon><Search /></el-icon>检索</button>
      </div>
      <div class="hero-examples">
        <span>试试：</span>
        <button v-for="e in examples" :key="e" class="chip" @click="kw = e; go()">{{ e }}</button>
      </div>
      <div class="hero-links">
        <router-link to="/advanced"><el-icon><Operation /></el-icon>高级检索</router-link>
        <router-link to="/advanced?tab=pico"><el-icon><List /></el-icon>PICOS 检索</router-link>
        <router-link to="/compare"><el-icon><DataAnalysis /></el-icon>跨指南推荐对比</router-link>
      </div>
    </div>
  </section>

  <div class="page">
    <div class="stats">
      <div class="stat" v-for="st in statItems" :key="st.label">
        <div class="stat-num">{{ fmt(st.value) }}</div>
        <div class="stat-label">{{ st.label }}</div>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8"><div class="card"><h3 class="section-title">指南年度分布</h3><div ref="yearRef" class="chart" /></div></el-col>
      <el-col :span="8"><div class="card"><h3 class="section-title">专科分布</h3><div ref="domainRef" class="chart" /></div></el-col>
      <el-col :span="8"><div class="card"><h3 class="section-title">推荐强度分布</h3><div ref="strengthRef" class="chart" /></div></el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="card"><h3 class="section-title">高频中成药</h3>
          <div class="tag-row"><el-tag v-for="d in s.topDrug" :key="d.term" type="success" effect="plain" class="hot-tag" @click="$router.push(`/entity/drug/${encodeURIComponent(d.term)}`)">{{ d.term }} <span class="muted">{{ d.n }}</span></el-tag></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card"><h3 class="section-title">高频疾病</h3>
          <div class="tag-row"><el-tag v-for="d in s.topDisease" :key="d.term" type="danger" effect="plain" class="hot-tag" @click="$router.push(`/entity/disease/${encodeURIComponent(d.term)}`)">{{ d.term }} <span class="muted">{{ d.n }}</span></el-tag></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import echarts from "@/chartTheme";
import { stats, suggest } from "@/api";
import { CTX, STRENGTH, STRENGTH_COLOR } from "@/labels";
import Logo from "@/components/Logo.vue";
const router = useRouter();
const kw = ref(""); const s = ref({});
const examples = ["麝香保心丸", "咳嗽变异性哮喘", "气阴两虚证", "慢性阻塞性肺疾病"];
const yearRef = ref(); const domainRef = ref(); const strengthRef = ref();
const statItems = computed(() => {
  const c = s.value.counts || {};
  return [
    { label: "指南与共识", value: c.guidelines },
    { label: "推荐意见", value: c.recommendations },
    { label: "原文段落", value: c.passages },
    { label: "参考文献", value: c.references },
  ];
});
const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("zh-CN"));
async function fetchSuggest(q, cb) { if (!q) return cb([]); cb(await suggest(q)); }
function onSelect(item) { item.type === "guideline" ? router.push(`/guideline/${item.id}`) : router.push(`/entity/${item.type}/${encodeURIComponent(item.term)}`); }
function go() { if (kw.value) router.push({ path: "/search", query: { q: kw.value } }); }
function draw(el, opt) { const c = echarts.init(el, "ebtcm"); c.setOption(opt); window.addEventListener("resize", () => c.resize()); }
onMounted(async () => {
  s.value = await stats();
  draw(yearRef.value, { tooltip: { trigger: "axis" }, grid: { left: 36, right: 12, top: 12, bottom: 24 }, xAxis: { type: "category", data: s.value.byYear.map((x) => x.year) }, yAxis: { type: "value" }, series: [{ type: "line", areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(42,96,148,.28)" }, { offset: 1, color: "rgba(42,96,148,0)" }] } }, data: s.value.byYear.map((x) => x.n) }] });
  draw(domainRef.value, { tooltip: {}, grid: { left: 70, right: 16, top: 6, bottom: 24 }, xAxis: { type: "value" }, yAxis: { type: "category", data: s.value.byDomain.slice(0, 10).map((x) => x.domain).reverse() }, series: [{ type: "bar", data: s.value.byDomain.slice(0, 10).map((x) => x.n).reverse() }] });
  draw(strengthRef.value, { tooltip: { trigger: "item" }, legend: { bottom: 0, itemGap: 14 }, series: [{ type: "pie", radius: ["42%", "68%"], center: ["50%", "44%"], label: { show: false }, data: s.value.byStrength.map((x) => ({ name: STRENGTH[x.strength], value: x.n, itemStyle: { color: STRENGTH_COLOR[x.strength] } })) }] });
});
</script>

<style scoped>
.hero { position: relative; overflow: hidden; color: #fff; padding: 64px 20px 52px; background: linear-gradient(135deg, #16344f 0%, #1f4e79 55%, #2a6094 100%); }
.hero::before { content: ""; position: absolute; inset: 0; background: radial-gradient(600px 300px at 15% 110%, rgba(224, 168, 63, 0.22), transparent 60%), radial-gradient(500px 260px at 90% -10%, rgba(255, 255, 255, 0.14), transparent 60%); pointer-events: none; }
.hero::after { content: ""; position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px); background-size: 32px 32px; mask-image: linear-gradient(180deg, rgba(0,0,0,.6), transparent); pointer-events: none; }
.hero-inner { position: relative; z-index: 1; max-width: 860px; margin: 0 auto; text-align: center; }
.hero-eyebrow { display: inline-flex; align-items: center; gap: 10px; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,.75); margin-bottom: 14px; }
.hero-title { font-family: var(--font-serif); font-size: 42px; font-weight: 700; letter-spacing: 4px; margin: 0; color: #fff; line-height: 1.25; }
.hero-sub { margin: 12px 0 28px; font-size: 15px; color: rgba(255,255,255,.82); }
.hero-search-row { display: flex; box-shadow: 0 10px 30px rgba(0,0,0,.2); border-radius: 12px; }
.hero-btn { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; flex-shrink: 0; border: none; border-radius: 0 12px 12px 0; background: var(--c-accent); color: #fff; height: 52px; padding: 0 28px; font-size: 15px; font-weight: 600; cursor: pointer; font-family: inherit; transition: background 0.15s var(--ease); }
.hero-btn:hover { background: #a56b18; }
.hero-btn:focus-visible { outline: 2px solid #fff; outline-offset: -4px; }
.hero-examples { margin-top: 16px; display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; font-size: 13px; color: rgba(255,255,255,.7); }
.chip { border: 1px solid rgba(255,255,255,.28); background: rgba(255,255,255,.1); color: #fff; font-size: 13px; padding: 4px 12px; border-radius: 999px; cursor: pointer; transition: background 0.15s var(--ease), border-color 0.15s var(--ease); font-family: inherit; }
.chip:hover { background: rgba(255,255,255,.22); border-color: rgba(255,255,255,.5); }
.hero-links { margin-top: 26px; display: flex; justify-content: center; gap: 28px; flex-wrap: wrap; }
.hero-links a { display: inline-flex; align-items: center; gap: 6px; color: rgba(255,255,255,.9); font-size: 14px; font-weight: 500; padding-bottom: 2px; border-bottom: 1px solid transparent; transition: border-color 0.15s var(--ease); }
.hero-links a:hover { color: #fff; border-bottom-color: var(--c-accent); }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: -46px; position: relative; z-index: 2; }
.stat { background: #fff; border: 1px solid var(--c-border); border-radius: var(--radius); padding: 18px 20px; box-shadow: var(--shadow-md); text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; color: var(--c-primary); font-variant-numeric: tabular-nums; letter-spacing: 0.5px; line-height: 1.2; }
.stat-label { margin-top: 4px; font-size: 13px; color: var(--c-text-3); letter-spacing: 1px; }
.hot-tag { cursor: pointer; transition: transform 0.15s var(--ease), box-shadow 0.15s var(--ease); }
.hot-tag:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
@media (max-width: 900px) { .stats { grid-template-columns: repeat(2, 1fr); } .hero-title { font-size: 32px; } }
</style>

<style>
/* el-autocomplete 不透传 scoped 属性，这里用全局样式 */
.hero-search { flex: 1; }
.hero-search .el-input__inner { height: 50px; line-height: 50px; }
.hero-search .el-input__wrapper { border-radius: 12px 0 0 12px; box-shadow: none; padding-left: 16px; font-size: 15px; }
.hero-search .el-input__wrapper.is-focus { box-shadow: inset 0 0 0 2px var(--c-accent-100); }
</style>
