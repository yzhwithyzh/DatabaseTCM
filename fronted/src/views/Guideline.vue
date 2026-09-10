<template>
  <div class="page" v-loading="loading">
    <el-row :gutter="16" v-if="d.guideline">
      <!-- 左：目录 -->
      <el-col :span="5">
        <div class="card sticky">
          <div class="facet-title">导航</div>
          <div class="facet-item" :class="{ active: view === 'info' }" @click="view = 'info'">基本信息</div>
          <div class="facet-item" :class="{ active: view === 'reco' }" @click="view = 'reco'">推荐意见（{{ d.recommendations.length }}）</div>
          <div class="facet-item" :class="{ active: view === 'text' }" @click="view = 'text'">正文</div>
        </div>
      </el-col>

      <!-- 中：内容 -->
      <el-col :span="14">
        <div class="card">
          <h2 class="page-title">{{ d.guideline.title }}</h2>
          <div class="result-meta" style="margin-top: 10px">
            <el-tag size="small">{{ GTYPE[d.guideline.guidelineType] }}</el-tag>
            <span>{{ d.guideline.publicationYear || "年份未知" }}</span>
            <span v-if="d.guideline.organization">{{ d.guideline.organization }}</span>
            <el-tag size="small" :type="d.guideline.status === 'current' ? 'success' : 'warning'">{{ STATUS[d.guideline.status] }}</el-tag>
          </div>
          <el-alert v-if="d.versions.length" type="info" :closable="false" style="margin: 8px 0">
            相关版本：<router-link v-for="v in d.versions" :key="v.id" :to="'/guideline/' + v.id" style="margin-right: 12px">{{ v.title }}（{{ v.publicationYear }}，{{ STATUS[v.status] }}）</router-link>
          </el-alert>

          <!-- 基本信息 -->
          <div v-show="view === 'info'">
            <h3 class="section-title" style="margin-top: 16px">基本信息</h3>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="引文">{{ d.guideline.citation }}</el-descriptions-item>
              <el-descriptions-item label="制定机构">{{ d.guideline.organization || "-" }}</el-descriptions-item>
              <el-descriptions-item label="作者">{{ (d.guideline.authors || []).join("，") || "-" }}</el-descriptions-item>
              <el-descriptions-item label="发布年份">{{ d.guideline.publicationYear || "-" }}</el-descriptions-item>
              <el-descriptions-item label="专科">{{ d.guideline.domain || "-" }}</el-descriptions-item>
              <el-descriptions-item label="DOI"><a v-if="d.guideline.doi" :href="'https://doi.org/' + d.guideline.doi" target="_blank">{{ d.guideline.doi }}</a><span v-else>-</span></el-descriptions-item>
              <el-descriptions-item label="关键词"><span class="tag-row" v-if="d.guideline.keywords?.length"><el-tag v-for="k in d.guideline.keywords" :key="k" size="small" effect="plain">{{ k }}</el-tag></span><span v-else>-</span></el-descriptions-item>
              <el-descriptions-item label="摘要">{{ d.guideline.abstract || firstAbstract || "-" }}</el-descriptions-item>
            </el-descriptions>
            <h3 class="section-title" style="margin-top: 16px">涉及实体</h3>
            <div class="tag-row">
              <el-tag v-for="(e, i) in entities" :key="i" :type="CTX_TAG[e.type]" effect="plain" style="cursor: pointer" @click="$router.push(`/entity/${e.type}/${encodeURIComponent(e.text)}`)">{{ CTX[e.type] }}：{{ e.text }} <span class="muted">{{ e.n }}</span></el-tag>
            </div>
          </div>

          <!-- 推荐意见 -->
          <div v-show="view === 'reco'">
            <div style="margin: 12px 0">
              <el-radio-group v-model="strengthFilter" size="small">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button v-for="(v, k) in STRENGTH" :key="k" :value="k">{{ v }}</el-radio-button>
              </el-radio-group>
            </div>
            <RecoCard v-for="r in recos" :key="r.id" :r="r" :show-guideline="false" />
          </div>

          <!-- 正文：直接展示 PDF -->
          <div v-if="view === 'text'" style="margin-top: 12px">
            <iframe :src="pdfSrc" class="pdf-frame" title="指南原文 PDF" />
          </div>
        </div>
      </el-col>

      <!-- 右：统计 -->
      <el-col :span="5">
        <div class="card">
          <h3 class="section-title">推荐强度分布</h3>
          <div v-for="(n, k) in strengthCount" :key="k" class="facet-item" @click="view = 'reco'; strengthFilter = k"><span>{{ STRENGTH[k] }}</span><span class="muted">{{ n }}</span></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { getGuideline, pdfUrl } from "@/api";
import { GTYPE, STATUS, STRENGTH, CTX, CTX_TAG } from "@/labels";
import RecoCard from "@/components/RecoCard.vue";
const route = useRoute();
const d = ref({}); const loading = ref(true); const view = ref("info"); const strengthFilter = ref(""); const pdfPage = ref(null);
// 正文 PDF 地址；从检索结果带 ?seq= 进来时定位到该段落所在页
const pdfSrc = computed(() => pdfUrl(route.params.id) + (pdfPage.value ? `#page=${pdfPage.value}` : ""));
const recos = computed(() => (d.value.recommendations || []).filter((r) => !strengthFilter.value || r.strength === strengthFilter.value));
const strengthCount = computed(() => { const m = {}; (d.value.recommendations || []).forEach((r) => (m[r.strength] = (m[r.strength] || 0) + 1)); return m; });
const firstAbstract = computed(() => (d.value.passages || []).find((p) => /摘要|Abstract/.test(p.text || ""))?.text?.slice(0, 600));
const entities = computed(() => {
  const m = {};
  (d.value.recommendations || []).forEach((r) => (r.contexts || []).forEach((c) => { if (c.type !== "outcome") { const k = c.type + "|" + c.text; m[k] = m[k] || { ...c, n: 0 }; m[k].n++; } }));
  return Object.values(m).sort((a, b) => b.n - a.n).slice(0, 30);
});
onMounted(async () => {
  d.value = await getGuideline(route.params.id); loading.value = false;
  if (route.query.seq) {
    const p = (d.value.passages || []).find((x) => x.sequenceNo === Number(route.query.seq));
    const n = parseInt(String(p?.page || "").replace(/\D/g, ""), 10);
    if (n > 0) pdfPage.value = n;
    view.value = "text";
  }
});
</script>

<style scoped>
.sticky { position: sticky; top: 16px; max-height: calc(100vh - 32px); overflow: auto; }
.pdf-frame { width: 100%; height: calc(100vh - 120px); min-height: 600px; border: 1px solid #e5e7eb; border-radius: 4px; background: #f5f5f5; }
</style>
