<template>
  <div class="reco" :class="['s-' + r.strength, { 'd-against': r.direction === 'against' }]">
    <div class="text" v-html="highlight(r.textOriginal, q)" />
    <div class="grade">
      <el-tag size="small" :type="STRENGTH_TAG[r.strength]">{{ STRENGTH[r.strength] }}</el-tag>
      <el-tag size="small" type="info" effect="plain">证据 {{ CERTAINTY[r.certainty] }}</el-tag>
      <el-tag size="small" v-if="r.direction === 'against'" type="danger">不推荐</el-tag>
      <span class="muted" v-if="r.gradingOriginal">原文分级：{{ r.gradingOriginal }}</span>
      <span class="muted" v-if="r.label">{{ r.label }}</span>
      <span class="muted">{{ r.sourcePage }}</span>
    </div>
    <div class="tag-row" style="margin-top: 6px">
      <el-tag v-for="(c, i) in r.contexts" :key="i" size="small" :type="CTX_TAG[c.type]" effect="plain" class="ctx" @click="goEntity(c)" style="cursor: pointer">
        {{ CTX[c.type] }}：{{ c.text }}
      </el-tag>
    </div>
    <div class="detail" v-if="r.conditions"><b>适用条件：</b>{{ r.conditions }}</div>
    <div class="detail" v-if="r.dosage"><b>用法用量：</b>{{ r.dosage }}</div>
    <el-collapse v-if="r.evidenceSummary || r.safetySummary || r.references?.length" class="more">
      <el-collapse-item title="证据与文献">
        <div class="detail" v-if="r.evidenceSummary"><b>证据描述：</b>{{ r.studyType || "" }} {{ r.studyCount ? r.studyCount + " 项研究" : "" }} {{ r.sampleSize ? r.sampleSize + " 例" : "" }}。{{ r.evidenceSummary }}</div>
        <div class="detail" v-if="r.safetySummary"><b>安全性：</b>{{ r.safetySummary }}</div>
        <div class="detail" v-if="r.references?.length"><b>引用文献：</b>
          <div v-for="f in r.references" :key="f.refNumber">[{{ f.refNumber }}] {{ f.citation }} <a v-if="f.doi" :href="'https://doi.org/' + f.doi" target="_blank">DOI</a></div>
        </div>
      </el-collapse-item>
    </el-collapse>
    <div class="muted" style="margin-top: 6px" v-if="showGuideline">
      来源：<router-link :to="'/guideline/' + r.guidelineId">{{ r.guidelineTitle }}</router-link>（{{ r.publicationYear }}）
      <el-tag v-if="r.guidelineStatus === 'superseded'" size="small" type="warning" style="margin-left: 6px">旧版</el-tag>
    </div>
  </div>
</template>

<script setup>
import { STRENGTH, STRENGTH_TAG, CERTAINTY, CTX, CTX_TAG, highlight } from "@/labels";
const props = defineProps({ r: Object, q: { type: String, default: "" }, showGuideline: { type: Boolean, default: true } });
const router = useRouter();
function goEntity(c) { router.push(`/entity/${c.type}/${encodeURIComponent(c.text)}`); }
</script>

<style scoped>
.more { border: none; margin-top: 6px; --el-collapse-header-height: 32px; }
.more :deep(.el-collapse-item__header) { font-size: 13px; color: var(--c-primary-600); font-weight: 500; border-bottom: none; }
.more :deep(.el-collapse-item__wrap) { border-bottom: none; }
.more :deep(.el-collapse-item__content) { padding-bottom: 6px; }
.ctx { cursor: pointer; }
</style>
