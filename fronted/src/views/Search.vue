<template>
  <div class="page">
    <el-row :gutter="16">
      <!-- 左：分面筛选 -->
      <el-col :span="5">
        <div class="card">
          <div class="facet-title">年份</div>
          <div class="facet-item" :class="{ active: !f.yearFrom }" @click="setYear(null)"><span>全部</span></div>
          <div v-for="y in (facets.year || []).slice(0, showYears)" :key="y.key" class="facet-item" :class="{ active: f.yearFrom === y.key }" @click="setYear(y.key)"><span>{{ y.key }} 年</span><span class="muted">{{ y.n }}</span></div>
          <div class="muted" style="cursor: pointer" v-if="(facets.year || []).length > showYears" @click="showYears = 99">更多 ›</div>
          <div class="facet-title">文献类型</div>
          <div class="facet-item" :class="{ active: !f.guidelineType }" @click="setF('guidelineType', null)"><span>全部</span></div>
          <div v-for="t in facets.type" :key="t.key" class="facet-item" :class="{ active: f.guidelineType === t.key }" @click="setF('guidelineType', t.key)"><span>{{ GTYPE[t.key] }}</span><span class="muted">{{ t.n }}</span></div>
          <div class="facet-title">专科</div>
          <div class="facet-item" :class="{ active: !f.domain }" @click="setF('domain', null)"><span>全部</span></div>
          <div v-for="t in facets.domain" :key="t.key" class="facet-item" :class="{ active: f.domain === t.key }" @click="setF('domain', t.key)"><span>{{ t.key }}</span><span class="muted">{{ t.n }}</span></div>
          <template v-if="f.scope === 'recommendation'">
            <div class="facet-title">推荐强度</div>
            <div class="facet-item" :class="{ active: !f.strength }" @click="setF('strength', null)"><span>全部</span></div>
            <div v-for="t in facets.strength" :key="t.key" class="facet-item" :class="{ active: f.strength === t.key }" @click="setF('strength', t.key)"><span>{{ STRENGTH[t.key] }}</span><span class="muted">{{ t.n }}</span></div>
            <div class="facet-title">证据确信度</div>
            <div class="facet-item" :class="{ active: !f.certainty }" @click="setF('certainty', null)"><span>全部</span></div>
            <div v-for="t in facets.certainty" :key="t.key" class="facet-item" :class="{ active: f.certainty === t.key }" @click="setF('certainty', t.key)"><span>{{ CERTAINTY[t.key] }}</span><span class="muted">{{ t.n }}</span></div>
          </template>
          <template v-if="f.scope === 'passage'">
            <div class="facet-title">内容类型</div>
            <div class="facet-item" :class="{ active: !f.passageType }" @click="setF('passageType', null)"><span>全部</span></div>
            <div v-for="t in facets.passageType" :key="t.key" class="facet-item" :class="{ active: f.passageType === t.key }" @click="setF('passageType', t.key)"><span>{{ PTYPE[t.key] }}</span><span class="muted">{{ t.n }}</span></div>
          </template>
          <div class="facet-title" v-if="facets.organization?.length">制定机构</div>
          <div v-for="t in facets.organization" :key="t.key" class="facet-item" :class="{ active: f.organization === t.key }" @click="setF('organization', f.organization === t.key ? null : t.key)"><span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px">{{ t.key }}</span><span class="muted">{{ t.n }}</span></div>
        </div>
      </el-col>

      <!-- 中：结果 -->
      <el-col :span="13">
        <div class="card">
          <div class="toolbar">
            <div class="toolbar-row">
              <span class="toolbar-label">检索条件</span>
              <el-tag v-if="f.q" closable @close="f.q = ''; run()">关键词：{{ f.q }}</el-tag>
              <el-tag v-if="f.domain" closable type="info" @close="setF('domain', null)">{{ f.domain }}</el-tag>
              <el-tag v-if="f.yearFrom" closable type="info" @close="setYear(null)">{{ f.yearFrom }} 年</el-tag>
              <span v-if="!f.q && !f.domain && !f.yearFrom" class="muted">全部</span>
              <span style="margin-left: auto" class="muted">共 <span class="count-strong">{{ total }}</span> 条</span>
            </div>
            <div class="toolbar-row">
              <el-radio-group v-model="f.scope" @change="run">
                <el-radio-button value="guideline">指南</el-radio-button>
                <el-radio-button value="recommendation">推荐意见</el-radio-button>
                <el-radio-button value="passage">原文段落</el-radio-button>
              </el-radio-group>
              <el-select v-model="f.sort" style="width: 130px; margin-left: auto" @change="run">
                <el-option label="按相关度" value="relevance" /><el-option label="年份降序" value="year_desc" /><el-option label="年份升序" value="year_asc" />
              </el-select>
            </div>
          </div>

          <div v-loading="loading" style="min-height: 300px">
            <!-- 指南 -->
            <template v-if="f.scope === 'guideline'">
              <div v-for="r in rows" :key="r.id" class="result-item">
                <div class="result-title"><router-link :to="'/guideline/' + r.id" v-html="highlight(r.title, f.q)" /></div>
                <div class="result-meta">
                  <span><el-tag size="small" effect="plain">{{ GTYPE[r.guidelineType] }}</el-tag></span>
                  <span v-if="r.organization">机构：{{ r.organization }}</span>
                  <span>发布：{{ r.publicationYear || "-" }}</span>
                  <span v-if="r.domain">专科：{{ r.domain }}</span>
                  <span>推荐意见 {{ r.recommendationCount }} 条</span>
                  <el-tag v-if="r.status === 'superseded'" size="small" type="warning">已被新版替代</el-tag>
                </div>
                <div class="result-snippet" v-if="r.snippet" v-html="highlight(r.snippet, f.q)" />
                <div class="muted" style="margin-top: 4px" v-if="r.topDrugs">涉及中成药：{{ r.topDrugs }}<span v-if="r.topDiseases">　疾病：{{ r.topDiseases }}</span></div>
              </div>
            </template>
            <!-- 推荐意见 -->
            <template v-else-if="f.scope === 'recommendation'">
              <RecoCard v-for="r in rows" :key="r.id" :r="r" :q="f.q" />
            </template>
            <!-- 段落 -->
            <template v-else>
              <div v-for="r in rows" :key="r.id" class="result-item">
                <div class="muted"><router-link :to="'/guideline/' + r.guidelineId + '?seq=' + r.sequenceNo">{{ r.guidelineTitle }}</router-link>（{{ r.publicationYear }}）· {{ r.sectionPath || "" }} · {{ r.page }}</div>
                <div class="result-snippet" v-html="highlight(r.snippet, f.q)" />
              </div>
            </template>
            <el-empty v-if="!loading && !rows.length" description="没有找到结果" />
          </div>
          <el-pagination style="margin-top: 12px; justify-content: flex-end" background layout="total, sizes, prev, pager, next" :total="total"
            v-model:current-page="f.pageNum" v-model:page-size="f.pageSize" :page-sizes="[10, 20, 50]" @change="run" />
        </div>
      </el-col>

      <!-- 右：图表 -->
      <el-col :span="6">
        <div class="card"><h3 class="section-title">命中结果年度趋势</h3><div ref="trendRef" class="chart" /></div>
        <div class="card" style="margin-top: 16px"><h3 class="section-title">类型分布</h3><div ref="typeRef" class="chart" /></div>
        <div class="card" style="margin-top: 16px" v-if="f.scope === 'recommendation'"><h3 class="section-title">推荐强度分布</h3><div ref="strengthRef" class="chart" /></div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import echarts from "@/chartTheme";
import { search } from "@/api";
import { GTYPE, STRENGTH, STRENGTH_COLOR, CERTAINTY, PTYPE, highlight } from "@/labels";
import RecoCard from "@/components/RecoCard.vue";

const route = useRoute(); const router = useRouter();
const f = reactive({ q: route.query.q || "", scope: route.query.scope || "guideline", guidelineType: null, domain: null, organization: null, yearFrom: null, yearTo: null,
  strength: null, certainty: null, passageType: null, sort: "relevance", pageNum: 1, pageSize: 20 });
const rows = ref([]); const total = ref(0); const facets = ref({}); const loading = ref(false); const showYears = ref(8);
const trendRef = ref(); const typeRef = ref(); const strengthRef = ref();
let charts = {};

function setF(k, v) { f[k] = v; f.pageNum = 1; run(); }
function setYear(y) { f.yearFrom = y; f.yearTo = y; f.pageNum = 1; run(); }
async function run() {
  loading.value = true;
  const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== null && v !== ""));
  const d = await search(params);
  rows.value = d.rows; total.value = d.total; facets.value = d.facets; loading.value = false;
  router.replace({ query: { q: f.q || undefined, scope: f.scope } });
  await nextTick(); drawCharts();
}
function draw(key, el, opt) { if (!el) return; charts[key] = charts[key] || echarts.init(el, "ebtcm"); charts[key].setOption(opt, true); }
function drawCharts() {
  const yr = [...(facets.value.year || [])].sort((a, b) => a.key - b.key);
  draw("trend", trendRef.value, { tooltip: { trigger: "axis" }, grid: { left: 32, right: 8, top: 10, bottom: 22 }, xAxis: { type: "category", data: yr.map((x) => x.key) }, yAxis: { type: "value" }, series: [{ type: "line", smooth: true, areaStyle: {}, data: yr.map((x) => x.n) }] });
  draw("type", typeRef.value, { tooltip: {}, grid: { left: 60, right: 8, top: 10, bottom: 22 }, xAxis: { type: "value" }, yAxis: { type: "category", data: (facets.value.type || []).map((x) => GTYPE[x.key]) }, series: [{ type: "bar", data: (facets.value.type || []).map((x) => x.n) }] });
  if (f.scope === "recommendation") draw("strength", strengthRef.value, { tooltip: { trigger: "item" }, legend: { bottom: 0, itemGap: 12 }, series: [{ type: "pie", radius: ["42%", "68%"], center: ["50%", "44%"], label: { show: false }, data: (facets.value.strength || []).map((x) => ({ name: STRENGTH[x.key], value: x.n, itemStyle: { color: STRENGTH_COLOR[x.key] } })) }] });
}
onMounted(run);
</script>

<style scoped>
.toolbar { margin-bottom: 8px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 0; }
.toolbar-row + .toolbar-row { border-top: 1px solid var(--c-border); }
.toolbar-label { font-size: 13px; font-weight: 600; color: var(--c-text-2); margin-right: 4px; }
</style>
