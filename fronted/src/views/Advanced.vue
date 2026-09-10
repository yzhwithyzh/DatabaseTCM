<template>
  <div class="page">
    <div class="card">
      <el-tabs v-model="tab">
        <!-- 高级搜索 -->
        <el-tab-pane label="高级搜索" name="advanced">
          <div class="cond-box">
            <div class="muted" style="margin-bottom: 8px">请输入搜索条件：</div>
            <div v-for="(c, i) in conds" :key="i" class="cond-row">
              <el-select v-if="i > 0" v-model="c.logic" style="width: 90px"><el-option label="并且" value="and" /><el-option label="或者" value="or" /><el-option label="不含" value="not" /></el-select>
              <span v-else style="width: 90px; display: inline-block"></span>
              <el-select v-model="c.field" style="width: 130px">
                <el-option label="题名" value="title" /><el-option label="关键词（题名+推荐）" value="keyword" /><el-option label="制定机构" value="organization" />
                <el-option label="专科" value="domain" /><el-option label="中成药" value="drug" /><el-option label="疾病" value="disease" /><el-option label="证候" value="syndrome" /><el-option label="正文" value="text" />
              </el-select>
              <el-select v-model="c.op" style="width: 100px"><el-option label="包含" value="contains" /><el-option label="不包含" value="not_contains" /><el-option label="等于" value="equals" /></el-select>
              <el-input v-model="c.value" placeholder="检索词" style="width: 300px" @keyup.enter="runAdvanced" />
              <el-button icon="Plus" circle @click="conds.splice(i + 1, 0, { logic: 'and', field: 'title', op: 'contains', value: '' })" />
              <el-button icon="Minus" circle :disabled="conds.length === 1" @click="conds.splice(i, 1)" />
            </div>
            <div class="cond-row">
              <span style="width: 90px; display: inline-block">发布年份：</span>
              <el-input-number v-model="adv.yearFrom" :controls="false" placeholder="起" style="width: 100px" />
              <span>-</span>
              <el-input-number v-model="adv.yearTo" :controls="false" placeholder="止" style="width: 100px" />
              <span style="margin-left: 16px">文献类型：</span>
              <el-select v-model="adv.guidelineType" clearable placeholder="全部" style="width: 130px"><el-option v-for="(v, k) in GTYPE" :key="k" :label="v" :value="k" /></el-select>
            </div>
            <div style="text-align: right; margin-top: 8px">
              <el-button @click="conds = [{ logic: 'and', field: 'title', op: 'contains', value: '' }]">清空</el-button>
              <el-button type="primary" @click="runAdvanced">搜索</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- PICOS -->
        <el-tab-pane label="PICOS 搜索" name="pico">
          <div class="cond-box">
            <el-form label-width="150px" :inline="false" style="max-width: 760px">
              <el-form-item label="P 人群 / 疾病"><el-input v-model="p.disease" placeholder="疾病，如 慢性阻塞性肺疾病" style="width: 260px" /> <el-input v-model="p.population" placeholder="人群限定，如 老年 / 儿童 / 稳定期" style="width: 260px; margin-left: 8px" /></el-form-item>
              <el-form-item label="I 干预（中成药）"><el-input v-model="p.intervention" placeholder="如 玉屏风颗粒 / 注射液" style="width: 528px" @keyup.enter="runPico" /></el-form-item>
              <el-form-item label="C 对照"><el-input v-model="p.comparator" placeholder="如 西医常规治疗 / 安慰剂（在原文中匹配）" style="width: 528px" /></el-form-item>
              <el-form-item label="O 结局"><el-input v-model="p.outcome" placeholder="如 急性加重次数 / 有效率 / 症状评分" style="width: 528px" /></el-form-item>
              <el-form-item label="S 证候 / 推荐强度">
                <el-input v-model="p.syndrome" placeholder="证候，如 肺脾气虚证" style="width: 260px" />
                <el-select v-model="p.strength" clearable placeholder="推荐强度" style="width: 200px; margin-left: 8px"><el-option v-for="(v, k) in STRENGTH" :key="k" :label="v" :value="k" /></el-select>
              </el-form-item>
              <el-form-item><el-button type="primary" @click="runPico">检索推荐意见</el-button></el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="card" style="margin-top: 16px" v-if="searched">
      <div style="margin-bottom: 8px; font-weight: 600">共找到 <span class="count-strong">{{ total }}</span> 条</div>
      <div v-loading="loading">
        <template v-if="tab === 'advanced'">
          <div v-for="r in rows" :key="r.id" class="result-item">
            <div class="result-title"><router-link :to="'/guideline/' + r.id">{{ r.title }}</router-link></div>
            <div class="result-meta"><span><el-tag size="small" effect="plain">{{ GTYPE[r.guidelineType] }}</el-tag></span><span v-if="r.organization">机构：{{ r.organization }}</span><span>发布：{{ r.publicationYear || "-" }}</span><span v-if="r.domain">专科：{{ r.domain }}</span><span>推荐意见 {{ r.recommendationCount }} 条</span></div>
            <div class="result-snippet" v-if="r.abstract">{{ r.abstract.slice(0, 200) }}…</div>
          </div>
        </template>
        <template v-else><RecoCard v-for="r in rows" :key="r.id" :r="r" /></template>
        <el-empty v-if="!loading && !rows.length" description="没有找到结果" />
      </div>
      <el-pagination style="margin-top: 12px; justify-content: flex-end" background layout="total, prev, pager, next" :total="total" v-model:current-page="pageNum" :page-size="20" @change="tab === 'advanced' ? runAdvanced() : runPico()" />
    </div>
  </div>
</template>

<script setup>
import { advanced, pico } from "@/api";
import { GTYPE, STRENGTH } from "@/labels";
import RecoCard from "@/components/RecoCard.vue";
const route = useRoute();
const tab = ref(route.query.tab === "pico" ? "pico" : "advanced");
const conds = ref([{ logic: "and", field: "title", op: "contains", value: "" }]);
const adv = reactive({ yearFrom: undefined, yearTo: undefined, guidelineType: undefined });
const p = reactive({ disease: "", population: "", intervention: "", comparator: "", outcome: "", syndrome: "", strength: undefined });
const rows = ref([]); const total = ref(0); const loading = ref(false); const searched = ref(false); const pageNum = ref(1);
async function runAdvanced() {
  const conditions = conds.value.filter((c) => c.value);
  if (!conditions.length) return;
  loading.value = true; searched.value = true;
  const d = await advanced({ conditions, yearFrom: adv.yearFrom || undefined, yearTo: adv.yearTo || undefined, guidelineType: adv.guidelineType || undefined, pageNum: pageNum.value, pageSize: 20 });
  rows.value = d.rows; total.value = d.total; loading.value = false;
}
async function runPico() {
  loading.value = true; searched.value = true;
  const params = Object.fromEntries(Object.entries(p).filter(([, v]) => v));
  const d = await pico({ ...params, pageNum: pageNum.value, pageSize: 20 });
  rows.value = d.rows; total.value = d.total; loading.value = false;
}
watch(tab, () => { searched.value = false; rows.value = []; pageNum.value = 1; });
</script>

<style scoped>
.cond-box { background: #f7f9fc; border: 1px solid var(--c-border); padding: 18px; border-radius: var(--radius-sm); }
.cond-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
</style>
