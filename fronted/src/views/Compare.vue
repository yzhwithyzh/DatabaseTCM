<template>
  <div class="page">
    <div class="card">
      <h3 class="section-title">跨指南推荐意见对比</h3>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <span>疾病</span><el-input v-model="q.disease" placeholder="如 冠心病心绞痛" style="width: 240px" clearable @keyup.enter="run" />
        <span>中成药</span><el-input v-model="q.drug" placeholder="如 麝香保心丸" style="width: 240px" clearable @keyup.enter="run" />
        <el-button type="primary" icon="Search" @click="run">对比</el-button>
        <span class="muted">至少填一项；同时填写时取交集。结果按指南分组，可比较不同年份、不同机构的推荐方向与强度。</span>
      </div>
    </div>

    <div class="card" style="margin-top: 16px" v-if="groups.length">
      <div class="summary">
        <span>共 {{ groups.length }} 篇指南、{{ groups.reduce((a, g) => a + g.items.length, 0) }} 条推荐</span>
        <span v-for="(n, k) in strengthTotal" :key="k"><el-tag size="small" :type="STRENGTH_TAG[k]">{{ STRENGTH[k] }}</el-tag> {{ n }}</span>
      </div>
      <el-table :data="matrix" border size="small" style="margin-top: 10px" max-height="300">
        <el-table-column prop="title" label="指南" min-width="280" show-overflow-tooltip>
          <template #default="{ row }"><router-link :to="'/guideline/' + row.id">{{ row.title }}</router-link></template>
        </el-table-column>
        <el-table-column prop="year" label="年份" width="70" />
        <el-table-column prop="organization" label="机构" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="80"><template #default="{ row }"><el-tag size="small" :type="row.status === 'current' ? 'success' : 'warning'">{{ STATUS[row.status] }}</el-tag></template></el-table-column>
        <el-table-column label="推荐数" width="70" prop="n" />
        <el-table-column label="强推荐" width="70" prop="strong" />
        <el-table-column label="弱推荐" width="70" prop="weak" />
        <el-table-column label="不推荐" width="70" prop="against" />
        <el-table-column label="涉及中成药" min-width="220" show-overflow-tooltip prop="drugs" />
      </el-table>

      <el-collapse style="margin-top: 16px">
        <el-collapse-item v-for="g in groups" :key="g.guidelineId" :name="g.guidelineId">
          <template #title><b>{{ g.title }}</b>&nbsp;<span class="muted">（{{ g.year }}，{{ g.organization || "机构未知" }}）· {{ g.items.length }} 条</span></template>
          <RecoCard v-for="r in g.items" :key="r.id" :r="r" :show-guideline="false" />
        </el-collapse-item>
      </el-collapse>
    </div>
    <el-empty v-else-if="searched" description="没有匹配的推荐意见" />
  </div>
</template>

<script setup>
import { compare } from "@/api";
import { STRENGTH, STRENGTH_TAG, STATUS } from "@/labels";
import RecoCard from "@/components/RecoCard.vue";
const route = useRoute();
const q = reactive({ disease: route.query.disease || "", drug: route.query.drug || "" });
const groups = ref([]); const searched = ref(false);
const matrix = computed(() => groups.value.map((g) => ({
  id: g.guidelineId, title: g.title, year: g.year, organization: g.organization, status: g.status, n: g.items.length,
  strong: g.items.filter((r) => r.strength === "strong").length, weak: g.items.filter((r) => r.strength === "weak").length,
  against: g.items.filter((r) => r.direction === "against").length,
  drugs: [...new Set(g.items.flatMap((r) => (r.contexts || []).filter((c) => c.type === "drug").map((c) => c.text)))].slice(0, 8).join("、"),
})));
const strengthTotal = computed(() => { const m = {}; groups.value.forEach((g) => g.items.forEach((r) => (m[r.strength] = (m[r.strength] || 0) + 1))); return m; });
async function run() {
  if (!q.disease && !q.drug) return;
  groups.value = await compare({ disease: q.disease || undefined, drug: q.drug || undefined }); searched.value = true;
}
onMounted(() => { if (q.disease || q.drug) run(); });
</script>

<style scoped>
.summary { display: flex; gap: 18px; align-items: center; }
</style>
