<template>
  <div class="app-container">
    <el-form :model="query" ref="queryRef" :inline="true">
      <el-form-item label="关键词" prop="keyword">
        <el-input v-model="query.keyword" placeholder="推荐原文" clearable style="width: 220px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="药品" prop="drug"><el-input v-model="query.drug" clearable style="width: 140px" @keyup.enter="handleQuery" /></el-form-item>
      <el-form-item label="疾病" prop="disease"><el-input v-model="query.disease" clearable style="width: 140px" @keyup.enter="handleQuery" /></el-form-item>
      <el-form-item label="强度" prop="strength">
        <el-select v-model="query.strength" clearable placeholder="全部" style="width: 110px"><el-option v-for="(v, k) in STRENGTH" :key="k" :label="v" :value="k" /></el-select>
      </el-form-item>
      <el-form-item label="确信度" prop="certainty">
        <el-select v-model="query.certainty" clearable placeholder="全部" style="width: 100px"><el-option v-for="(v, k) in CERTAINTY" :key="k" :label="v" :value="k" /></el-select>
      </el-form-item>
      <el-form-item label="方向" prop="direction">
        <el-select v-model="query.direction" clearable placeholder="全部" style="width: 100px"><el-option v-for="(v, k) in DIRECTION" :key="k" :label="v" :value="k" /></el-select>
      </el-form-item>
      <el-form-item label="核验" prop="verified">
        <el-select v-model="query.verified" clearable placeholder="全部" style="width: 100px"><el-option label="已核验" :value="true" /><el-option label="未核验" :value="false" /></el-select>
      </el-form-item>
      <el-form-item prop="quoteIssue"><el-checkbox v-model="query.quoteIssue" label="只看原文校验未通过" /></el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5"><el-button type="success" plain icon="Check" :disabled="!selected.length" @click="verify(true)" v-hasPermi="['ebtcm:recommendation:verify']">标记已核验</el-button></el-col>
      <el-col :span="1.5"><el-button type="warning" plain icon="Close" :disabled="!selected.length" @click="verify(false)" v-hasPermi="['ebtcm:recommendation:verify']">取消核验</el-button></el-col>
    </el-row>

    <el-table v-loading="loading" :data="list" @selection-change="(v) => (selected = v)">
      <el-table-column type="selection" width="45" />
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-descriptions :column="2" border size="small" class="expand">
            <el-descriptions-item label="所属指南" :span="2">{{ row.guidelineTitle }}（{{ row.publicationYear }}）· {{ row.sourcePage }}</el-descriptions-item>
            <el-descriptions-item label="推荐原文" :span="2">{{ row.textOriginal }}</el-descriptions-item>
            <el-descriptions-item label="原始分级">{{ row.gradingOriginal || "-" }}</el-descriptions-item>
            <el-descriptions-item label="抽取方式">{{ row.extractionMethod }} {{ row.sourceSection ? "· " + row.sourceSection : "" }}</el-descriptions-item>
            <el-descriptions-item label="适用条件" :span="2">{{ row.conditions || "-" }}</el-descriptions-item>
            <el-descriptions-item label="用法用量" :span="2">{{ row.dosage || "-" }}</el-descriptions-item>
            <el-descriptions-item label="证据描述" :span="2">{{ row.studyType || "" }} {{ row.studyCount ? row.studyCount + " 项" : "" }} {{ row.sampleSize ? row.sampleSize + " 例" : "" }} {{ row.evidenceSummary || "" }}</el-descriptions-item>
            <el-descriptions-item label="安全性" :span="2">{{ row.safetySummary || "-" }}</el-descriptions-item>
            <el-descriptions-item label="实体" :span="2">
              <el-tag v-for="(c, i) in row.contexts" :key="i" size="small" class="ctx" :type="CTX_TAG[c.type]">{{ CTX[c.type] }}：{{ c.text }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="引用文献" :span="2">
              <div v-for="r in row.references" :key="r.refNumber">[{{ r.refNumber }}] {{ r.citation }}</div>
              <span v-if="!row.references?.length">-</span>
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </el-table-column>
      <el-table-column label="推荐原文" prop="textOriginal" min-width="360" show-overflow-tooltip />
      <el-table-column label="指南" prop="guidelineTitle" min-width="200" show-overflow-tooltip />
      <el-table-column label="年份" prop="publicationYear" width="70" />
      <el-table-column label="方向" width="70"><template #default="{ row }">{{ DIRECTION[row.direction] }}</template></el-table-column>
      <el-table-column label="强度" width="80"><template #default="{ row }"><el-tag size="small" :type="STRENGTH_TAG[row.strength]">{{ STRENGTH[row.strength] }}</el-tag></template></el-table-column>
      <el-table-column label="确信度" width="70"><template #default="{ row }">{{ CERTAINTY[row.certainty] }}</template></el-table-column>
      <el-table-column label="核验" width="60" align="center"><template #default="{ row }"><el-icon v-if="row.verified" color="green"><Check /></el-icon></template></el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }"><el-button link type="primary" icon="Edit" @click="openEdit(row)" v-hasPermi="['ebtcm:recommendation:edit']">编辑</el-button></template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />

    <el-dialog title="修改推荐意见" v-model="editOpen" width="760px" append-to-body>
      <el-form :model="form" label-width="90px">
        <el-form-item label="编号"><el-input v-model="form.label" /></el-form-item>
        <el-form-item label="推荐原文"><el-input v-model="form.textOriginal" type="textarea" :rows="4" /></el-form-item>
        <el-row>
          <el-col :span="8"><el-form-item label="方向"><el-select v-model="form.direction"><el-option v-for="(v, k) in DIRECTION" :key="k" :label="v" :value="k" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="强度"><el-select v-model="form.strength"><el-option v-for="(v, k) in STRENGTH" :key="k" :label="v" :value="k" /></el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="确信度"><el-select v-model="form.certainty"><el-option v-for="(v, k) in CERTAINTY" :key="k" :label="v" :value="k" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="原始分级"><el-input v-model="form.gradingOriginal" /></el-form-item>
        <el-form-item label="适用条件"><el-input v-model="form.conditions" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="用法用量"><el-input v-model="form.dosage" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="证据描述"><el-input v-model="form.evidenceSummary" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="安全性"><el-input v-model="form.safetySummary" type="textarea" :rows="2" /></el-form-item>
        <el-row>
          <el-col :span="8"><el-form-item label="页码"><el-input v-model="form.sourcePage" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="已核验"><el-switch v-model="form.verified" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="启用"><el-switch v-model="form.isActive" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="EbtcmRecommendation">
import { listRecommendation, updateRecommendation, verifyRecommendation, STRENGTH, CERTAINTY, DIRECTION, STRENGTH_TAG } from "~/plugins/ebtcm/api/ebtcm";

const { proxy } = getCurrentInstance();
const CTX = { disease: "疾病", syndrome: "证候", drug: "药品", population: "人群", outcome: "结局" };
const CTX_TAG = { disease: "danger", syndrome: "warning", drug: "success", population: "info", outcome: "" };
const loading = ref(false); const list = ref([]); const total = ref(0); const selected = ref([]);
const query = reactive({ pageNum: 1, pageSize: 10, keyword: undefined, drug: undefined, disease: undefined, strength: undefined, certainty: undefined, direction: undefined, verified: undefined, quoteIssue: undefined });
const editOpen = ref(false); const form = ref({});

function getList() {
  loading.value = true;
  const params = { ...query, quoteIssue: query.quoteIssue || undefined };
  listRecommendation(params).then((res) => { list.value = res.rows; total.value = res.total; loading.value = false; });
}
function handleQuery() { query.pageNum = 1; getList(); }
function resetQuery() { proxy.resetForm("queryRef"); query.verified = undefined; query.quoteIssue = undefined; handleQuery(); }
function openEdit(row) { form.value = { ...row }; editOpen.value = true; }
function submitEdit() {
  const f = form.value;
  const data = { id: f.id, label: f.label, textOriginal: f.textOriginal, direction: f.direction, strength: f.strength, certainty: f.certainty, gradingOriginal: f.gradingOriginal,
    conditions: f.conditions, dosage: f.dosage, evidenceSummary: f.evidenceSummary, safetySummary: f.safetySummary, sourcePage: f.sourcePage, verified: f.verified, isActive: f.isActive };
  updateRecommendation(data).then(() => { proxy.$modal.msgSuccess("保存成功"); editOpen.value = false; getList(); });
}
function verify(flag) {
  verifyRecommendation(selected.value.map((x) => x.id), flag).then((res) => { proxy.$modal.msgSuccess(res.msg); getList(); });
}
getList();
</script>

<style scoped>
.expand { margin: 4px 20px; }
.ctx { margin: 2px 4px 2px 0; }
</style>
