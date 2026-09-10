<template>
  <div class="app-container">
    <el-row :gutter="16">
      <el-col :span="4" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ c.value ?? "-" }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt16">
      <el-col :span="12"><el-card shadow="never" header="指南年度分布"><div ref="yearRef" class="chart" /></el-card></el-col>
      <el-col :span="12"><el-card shadow="never" header="文献类型 / 推荐强度"><div ref="typeRef" class="chart" /></el-card></el-col>
    </el-row>
    <el-row :gutter="16" class="mt16">
      <el-col :span="12"><el-card shadow="never" header="专科分布"><div ref="domainRef" class="chart" /></el-card></el-col>
      <el-col :span="12"><el-card shadow="never" header="高频中成药（推荐意见涉及次数）"><div ref="drugRef" class="chart" /></el-card></el-col>
    </el-row>
    <el-row :gutter="16" class="mt16">
      <el-col :span="12">
        <el-card shadow="never" header="制定机构 TOP10">
          <el-table :data="stats.topOrganization" size="small">
            <el-table-column prop="organization" label="机构" show-overflow-tooltip />
            <el-table-column prop="n" label="指南数" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" header="数据质量待办">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="缺发布年份的指南">{{ stats.counts?.missingYear }}</el-descriptions-item>
            <el-descriptions-item label="缺制定机构的指南">{{ stats.counts?.missingOrg }}</el-descriptions-item>
            <el-descriptions-item label="原文校验未通过的推荐意见">{{ stats.counts?.quoteIssues }}</el-descriptions-item>
            <el-descriptions-item label="已人工核验的推荐意见">{{ stats.counts?.verified }} / {{ stats.counts?.recommendations }}</el-descriptions-item>
            <el-descriptions-item label="标准术语数">{{ stats.counts?.concepts }}（实体写法 {{ stats.counts?.contexts }} 条）</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="EbtcmDashboard">
import * as echarts from "echarts";
import { getStatsOverview, STRENGTH, GTYPE } from "~/plugins/ebtcm/api/ebtcm";

const stats = ref({});
const yearRef = ref(); const typeRef = ref(); const domainRef = ref(); const drugRef = ref();
const cards = computed(() => {
  const c = stats.value.counts || {};
  return [
    { label: "指南 / 共识", value: c.guidelines },
    { label: "推荐意见", value: c.recommendations },
    { label: "正文段落", value: c.passages },
    { label: "参考文献", value: c.references },
    { label: "实体写法", value: c.contexts },
    { label: "已核验推荐", value: c.verified },
  ];
});

function draw(el, option) {
  const chart = echarts.init(el);
  chart.setOption(option);
  window.addEventListener("resize", () => chart.resize());
}

onMounted(async () => {
  const res = await getStatsOverview();
  stats.value = res.data;
  const s = res.data;
  draw(yearRef.value, {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: s.byYear.map((x) => x.year) },
    yAxis: { type: "value" },
    series: [{ type: "line", smooth: true, areaStyle: {}, data: s.byYear.map((x) => x.n) }],
  });
  draw(typeRef.value, {
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      { type: "pie", radius: ["30%", "55%"], center: ["28%", "45%"], data: s.byType.map((x) => ({ name: GTYPE[x.type] || x.type, value: x.n })) },
      { type: "pie", radius: ["30%", "55%"], center: ["72%", "45%"], data: s.byStrength.map((x) => ({ name: STRENGTH[x.strength] || x.strength, value: x.n })) },
    ],
  });
  draw(domainRef.value, {
    tooltip: {},
    grid: { left: 80 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: s.byDomain.map((x) => x.domain).reverse() },
    series: [{ type: "bar", data: s.byDomain.map((x) => x.n).reverse() }],
  });
  draw(drugRef.value, {
    tooltip: {},
    grid: { left: 110 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: s.topDrug.map((x) => x.term).reverse() },
    series: [{ type: "bar", data: s.topDrug.map((x) => x.n).reverse(), itemStyle: { color: "#5B9BD5" } }],
  });
});
</script>

<style scoped>
.stat-card { text-align: center; }
.stat-value { font-size: 26px; font-weight: 600; color: #1f4e79; }
.stat-label { color: #888; margin-top: 4px; }
.chart { height: 280px; }
.mt16 { margin-top: 16px; }
</style>
