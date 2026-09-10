<template>
  <div class="page" v-loading="loading">
    <el-row :gutter="16">
      <el-col :span="17">
        <div class="card">
          <div style="display: flex; align-items: baseline; gap: 12px">
            <el-tag :type="CTX_TAG[type]" size="large">{{ CTX[type] }}</el-tag>
            <h2 class="page-title">{{ term }}</h2>
            <span class="muted" v-if="d.summary?.names?.length > 1">同义写法：{{ d.summary.names.filter((n) => n !== term).join("、") }}</span>
          </div>
          <div class="result-meta" style="margin: 10px 0">
            <span>涉及指南 <b>{{ d.summary?.guidelines }}</b> 篇</span>
            <span>推荐意见 <b>{{ d.total }}</b> 条</span>
            <router-link :to="type === 'drug' ? { path: '/compare', query: { drug: term } } : { path: '/compare', query: { disease: term } }" v-if="type === 'drug' || type === 'disease'">跨指南对比 ›</router-link>
          </div>
          <el-radio-group v-model="strength" size="small" @change="load(1)">
            <el-radio-button value="">全部强度</el-radio-button>
            <el-radio-button v-for="s in d.summary?.byStrength || []" :key="s.key" :value="s.key">{{ STRENGTH[s.key] }} ({{ s.n }})</el-radio-button>
          </el-radio-group>
          <div style="margin-top: 12px">
            <template v-for="g in grouped" :key="g.id">
              <div class="group-head">
                <router-link :to="'/guideline/' + g.id"><b>{{ g.title }}</b></router-link>
                <span class="muted">（{{ g.year }}{{ g.organization ? "，" + g.organization : "" }}）</span>
                <el-tag v-if="g.status === 'superseded'" size="small" type="warning">旧版</el-tag>
              </div>
              <RecoCard v-for="r in g.items" :key="r.id" :r="r" :show-guideline="false" />
            </template>
            <el-empty v-if="!loading && !d.rows?.length" description="暂无相关推荐意见" />
          </div>
          <el-pagination style="margin-top: 12px; justify-content: flex-end" background layout="total, prev, pager, next" :total="d.total || 0" :current-page="pageNum" :page-size="20" @current-change="load" />
        </div>
      </el-col>
      <el-col :span="7">
        <div class="card"><h3 class="section-title">推荐年度分布</h3><div ref="yearRef" class="chart" /></div>
        <div class="card" style="margin-top: 16px">
          <h3 class="section-title">相关实体</h3>
          <div class="tag-row">
            <el-tag v-for="(x, i) in d.summary?.related || []" :key="i" :type="CTX_TAG[x.type]" effect="plain" style="cursor: pointer" @click="$router.push(`/entity/${x.type}/${encodeURIComponent(x.term)}`)">{{ CTX[x.type] }}：{{ x.term }} <span class="muted">{{ x.n }}</span></el-tag>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import echarts from "@/chartTheme";
import { entity } from "@/api";
import { CTX, CTX_TAG, STRENGTH } from "@/labels";
import RecoCard from "@/components/RecoCard.vue";
const route = useRoute();
const type = route.params.type; const term = decodeURIComponent(route.params.term);
const d = ref({}); const loading = ref(true); const strength = ref(""); const pageNum = ref(1); const yearRef = ref(); let chart;
const grouped = computed(() => {
  const m = {};
  (d.value.rows || []).forEach((r) => { (m[r.guidelineId] = m[r.guidelineId] || { id: r.guidelineId, title: r.guidelineTitle, year: r.publicationYear, organization: r.organization, status: r.guidelineStatus, items: [] }).items.push(r); });
  return Object.values(m);
});
async function load(p = 1) {
  pageNum.value = p; loading.value = true;
  d.value = await entity(type, { term, strength: strength.value || undefined, pageNum: p, pageSize: 20 }); loading.value = false;
  await nextTick();
  const by = d.value.summary?.byYear || [];
  chart = chart || echarts.init(yearRef.value, "ebtcm");
  chart.setOption({ tooltip: { trigger: "axis" }, grid: { left: 30, right: 8, top: 10, bottom: 22 }, xAxis: { type: "category", data: by.map((x) => x.key) }, yAxis: { type: "value" }, series: [{ type: "bar", itemStyle: { borderRadius: [4, 4, 0, 0] }, data: by.map((x) => x.n) }] }, true);
}
onMounted(() => load(1));
</script>

<style scoped>
.group-head { margin: 18px 0 8px; padding-bottom: 6px; border-bottom: 1px solid var(--c-border); font-size: 15px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
</style>
