<template>
  <div class="app-container">
    <el-form :model="query" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="关键词" prop="keyword">
        <el-input v-model="query.keyword" placeholder="题名 / 机构 / 引文" clearable style="width: 240px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="类型" prop="guidelineType">
        <el-select v-model="query.guidelineType" clearable placeholder="全部" style="width: 130px">
          <el-option v-for="(v, k) in GTYPE" :key="k" :label="v" :value="k" />
        </el-select>
      </el-form-item>
      <el-form-item label="专科" prop="domain">
        <el-input v-model="query.domain" placeholder="如 呼吸" clearable style="width: 120px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="query.status" clearable placeholder="全部" style="width: 120px">
          <el-option label="现行" value="current" /><el-option label="已被替代" value="superseded" /><el-option label="撤回" value="withdrawn" />
        </el-select>
      </el-form-item>
      <el-form-item label="年份" prop="yearFrom">
        <el-input-number v-model="query.yearFrom" :min="1990" :max="2030" :controls="false" placeholder="起" style="width: 80px" />
        <span style="margin: 0 4px">-</span>
        <el-input-number v-model="query.yearTo" :min="1990" :max="2030" :controls="false" placeholder="止" style="width: 80px" />
      </el-form-item>
      <el-form-item label="待补" prop="missing">
        <el-select v-model="query.missing" clearable placeholder="缺失字段" style="width: 130px">
          <el-option label="缺年份" value="year" /><el-option label="缺机构" value="organization" />
          <el-option label="题名为编号" value="title" /><el-option label="缺专科" value="domain" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="list" @sort-change="onSort">
      <el-table-column label="题名" prop="title" min-width="320" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="openDetail(row)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="类型" prop="guidelineType" width="90"><template #default="{ row }">{{ GTYPE[row.guidelineType] }}</template></el-table-column>
      <el-table-column label="年份" prop="publicationYear" width="70"><template #default="{ row }">{{ row.publicationYear || "-" }}</template></el-table-column>
      <el-table-column label="专科" prop="domain" width="90" />
      <el-table-column label="制定机构" prop="organization" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" prop="status" width="90">
        <template #default="{ row }"><el-tag :type="row.status === 'current' ? 'success' : 'info'" size="small">{{ STATUS[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column label="推荐 / 已核验" width="110" align="center">
        <template #default="{ row }">{{ row.recommendationCount }} / {{ row.verifiedCount }}</template>
      </el-table-column>
      <el-table-column label="段落" prop="passageCount" width="70" align="center" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" icon="View" @click="openDetail(row)">详情</el-button>
          <el-button link type="primary" icon="Edit" @click="openEdit(row)" v-hasPermi="['ebtcm:guideline:edit']">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />

    <!-- 编辑 -->
    <el-dialog title="修改指南元数据" v-model="editOpen" width="720px" append-to-body>
      <el-form :model="form" label-width="90px">
        <el-form-item label="题名"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="制定机构"><el-input v-model="form.organization" /></el-form-item>
        <el-row>
          <el-col :span="8"><el-form-item label="类型">
            <el-select v-model="form.guidelineType"><el-option v-for="(v, k) in GTYPE" :key="k" :label="v" :value="k" /></el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="年份"><el-input-number v-model="form.publicationYear" :min="0" :max="2030" :controls="false" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="状态">
            <el-select v-model="form.status"><el-option label="现行" value="current" /><el-option label="已被替代" value="superseded" /><el-option label="撤回" value="withdrawn" /></el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="专科"><el-input v-model="form.domain" /></el-form-item>
        <el-form-item label="DOI"><el-input v-model="form.doi" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="authorsText" placeholder="逗号分隔" /></el-form-item>
        <el-form-item label="关键词"><el-input v-model="keywordsText" placeholder="逗号分隔" /></el-form-item>
        <el-form-item label="摘要"><el-input v-model="form.abstract" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-drawer v-model="detailOpen" size="70%" :title="bundle.guideline?.title">
      <div v-loading="detailLoading">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="类型">{{ GTYPE[bundle.guideline?.guidelineType] }}</el-descriptions-item>
          <el-descriptions-item label="年份">{{ bundle.guideline?.publicationYear }}</el-descriptions-item>
          <el-descriptions-item label="专科">{{ bundle.guideline?.domain }}</el-descriptions-item>
          <el-descriptions-item label="机构" :span="2">{{ bundle.guideline?.organization }}</el-descriptions-item>
          <el-descriptions-item label="DOI">{{ bundle.guideline?.doi }}</el-descriptions-item>
          <el-descriptions-item label="引文" :span="3">{{ bundle.guideline?.citation }}</el-descriptions-item>
        </el-descriptions>
        <el-tabs class="mt16">
          <el-tab-pane :label="`推荐意见 (${bundle.recommendations?.length || 0})`">
            <el-table :data="bundle.recommendations" size="small" max-height="520">
              <el-table-column prop="label" label="编号" width="90" />
              <el-table-column prop="textOriginal" label="推荐原文" min-width="380" show-overflow-tooltip />
              <el-table-column label="强度" width="80"><template #default="{ row }"><el-tag size="small" :type="STRENGTH_TAG[row.strength]">{{ STRENGTH[row.strength] }}</el-tag></template></el-table-column>
              <el-table-column label="确信度" width="70"><template #default="{ row }">{{ CERTAINTY[row.certainty] }}</template></el-table-column>
              <el-table-column prop="sourcePage" label="页码" width="60" />
              <el-table-column label="核验" width="60"><template #default="{ row }"><el-icon v-if="row.verified" color="green"><Check /></el-icon></template></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`段落 (${bundle.passages?.length || 0})`">
            <div class="passages">
              <div v-for="p in bundle.passages" :key="p.id" class="passage">
                <div class="passage-meta">{{ p.sectionPath || p.section }} · {{ p.page }} · {{ p.blockType }} · {{ p.textSource }}</div>
                <div v-if="p.tableHtml" v-html="p.tableHtml" class="table-html" />
                <div v-else>{{ p.text }}</div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="`参考文献 (${bundle.references?.length || 0})`">
            <el-table :data="bundle.references" size="small" max-height="520">
              <el-table-column prop="refNumber" label="#" width="50" />
              <el-table-column prop="citationText" label="文献" min-width="400" />
              <el-table-column prop="refType" label="类型" width="130" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`版本 (${bundle.versions?.length || 0})`">
            <el-table :data="bundle.versions" size="small">
              <el-table-column prop="title" label="题名" /><el-table-column prop="publicationYear" label="年份" width="80" /><el-table-column prop="status" label="状态" width="100" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>
  </div>
</template>

<script setup name="EbtcmGuideline">
import { listGuideline, getGuidelineBundle, updateGuideline, GTYPE, STRENGTH, CERTAINTY, STRENGTH_TAG } from "~/plugins/ebtcm/api/ebtcm";

const { proxy } = getCurrentInstance();
const STATUS = { current: "现行", superseded: "已被替代", withdrawn: "撤回" };
const loading = ref(false); const showSearch = ref(true);
const list = ref([]); const total = ref(0);
const query = reactive({ pageNum: 1, pageSize: 10, keyword: undefined, guidelineType: undefined, domain: undefined, status: undefined, yearFrom: undefined, yearTo: undefined, missing: undefined });
const editOpen = ref(false); const form = ref({}); const authorsText = ref(""); const keywordsText = ref("");
const detailOpen = ref(false); const detailLoading = ref(false); const bundle = ref({});

function getList() {
  loading.value = true;
  listGuideline(query).then((res) => { list.value = res.rows; total.value = res.total; loading.value = false; });
}
function handleQuery() { query.pageNum = 1; getList(); }
function resetQuery() { proxy.resetForm("queryRef"); query.yearFrom = undefined; query.yearTo = undefined; handleQuery(); }
function onSort() {}
function openEdit(row) {
  form.value = { ...row };
  authorsText.value = (row.authors || []).join(",");
  keywordsText.value = (row.keywords || []).join(",");
  editOpen.value = true;
}
function submitEdit() {
  const split = (s) => s ? s.split(/[,，;；]/).map((x) => x.trim()).filter(Boolean) : undefined;
  const data = { id: form.value.id, title: form.value.title, organization: form.value.organization, guidelineType: form.value.guidelineType,
    publicationYear: form.value.publicationYear, domain: form.value.domain, status: form.value.status, doi: form.value.doi,
    abstract: form.value.abstract, authors: split(authorsText.value), keywords: split(keywordsText.value) };
  updateGuideline(data).then(() => { proxy.$modal.msgSuccess("保存成功"); editOpen.value = false; getList(); });
}
function openDetail(row) {
  detailOpen.value = true; detailLoading.value = true; bundle.value = {};
  getGuidelineBundle(row.id).then((res) => { bundle.value = res.data; detailLoading.value = false; });
}
getList();
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.passages { max-height: 560px; overflow: auto; }
.passage { padding: 8px 4px; border-bottom: 1px dashed #eee; line-height: 1.6; }
.passage-meta { color: #999; font-size: 12px; margin-bottom: 4px; }
.table-html :deep(table) { border-collapse: collapse; font-size: 12px; }
.table-html :deep(td) { border: 1px solid #ddd; padding: 2px 6px; }
</style>
