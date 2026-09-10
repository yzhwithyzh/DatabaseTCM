<template>
  <div class="app-container">
    <el-row :gutter="16">
      <!-- 左：原始写法归一工作台 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <span>原始写法归一（按出现次数）</span>
          </template>
          <el-form :inline="true">
            <el-form-item label="实体类型">
              <el-select v-model="termQuery.contextType" style="width: 110px" @change="loadTerms">
                <el-option v-for="(v, k) in CTX" :key="k" :label="v" :value="k" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="termQuery.keyword" clearable style="width: 160px" @keyup.enter="loadTerms" placeholder="如 参麦" />
            </el-form-item>
            <el-form-item><el-button type="primary" icon="Search" @click="loadTerms">查询</el-button></el-form-item>
          </el-form>
          <el-table :data="terms" size="small" max-height="520" v-loading="termLoading" @selection-change="(v) => (termSel = v)">
            <el-table-column type="selection" width="40" />
            <el-table-column prop="term" label="原始写法" min-width="180" />
            <el-table-column prop="n" label="次数" width="70" align="right" />
            <el-table-column prop="guidelines" label="指南数" width="70" align="right" />
            <el-table-column label="已归一" width="110"><template #default="{ row }"><el-tag v-if="row.mapped" size="small" type="success">{{ row.conceptName }}</el-tag></template></el-table-column>
          </el-table>
          <div class="merge-bar">
            <el-input v-model="mergeName" placeholder="标准名（默认取选中的第一项）" style="width: 240px" />
            <el-button type="primary" :disabled="!termSel.length" @click="doMerge" v-hasPermi="['ebtcm:concept:edit']">归并选中 {{ termSel.length }} 项</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右：标准术语表 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <span>标准术语表</span>
            <el-button style="float: right" type="primary" size="small" icon="Plus" @click="openEdit()" v-hasPermi="['ebtcm:concept:add']">新增</el-button>
          </template>
          <el-form :inline="true">
            <el-form-item label="类型">
              <el-select v-model="query.conceptType" clearable style="width: 110px" @change="getList"><el-option v-for="(v, k) in CTX" :key="k" :label="v" :value="k" /></el-select>
            </el-form-item>
            <el-form-item label="关键词"><el-input v-model="query.keyword" clearable style="width: 160px" @keyup.enter="getList" /></el-form-item>
            <el-form-item><el-button type="primary" icon="Search" @click="getList">查询</el-button></el-form-item>
          </el-form>
          <el-table :data="list" size="small" v-loading="loading" max-height="470">
            <el-table-column label="类型" width="70"><template #default="{ row }">{{ CTX[row.conceptType] }}</template></el-table-column>
            <el-table-column prop="name" label="标准名" min-width="140" />
            <el-table-column label="同义词" min-width="200"><template #default="{ row }">{{ (row.synonyms || []).join("、") }}</template></el-table-column>
            <el-table-column prop="usageCount" label="引用" width="60" align="right" />
            <el-table-column label="操作" width="110">
              <template #default="{ row }">
                <el-button link type="primary" icon="Edit" @click="openEdit(row)" v-hasPermi="['ebtcm:concept:edit']">编辑</el-button>
                <el-button link type="danger" icon="Delete" @click="remove(row)" v-hasPermi="['ebtcm:concept:remove']">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog :title="form.id ? '修改术语' : '新增术语'" v-model="editOpen" width="520px" append-to-body>
      <el-form :model="form" label-width="80px">
        <el-form-item label="类型"><el-select v-model="form.conceptType"><el-option v-for="(v, k) in CTX" :key="k" :label="v" :value="k" /></el-select></el-form-item>
        <el-form-item label="标准名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="同义词"><el-input v-model="synText" type="textarea" :rows="3" placeholder="逗号分隔" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="EbtcmConcept">
import { listConcept, listContextTerms, saveConcept, mergeConcept, delConcept } from "~/plugins/ebtcm/api/ebtcm";

const { proxy } = getCurrentInstance();
const CTX = { drug: "药品", disease: "疾病", syndrome: "证候", population: "人群" };
const termQuery = reactive({ contextType: "drug", keyword: "", limit: 100 });
const terms = ref([]); const termLoading = ref(false); const termSel = ref([]); const mergeName = ref("");
const query = reactive({ pageNum: 1, pageSize: 10, keyword: undefined, conceptType: undefined });
const list = ref([]); const total = ref(0); const loading = ref(false);
const editOpen = ref(false); const form = ref({}); const synText = ref("");

function loadTerms() { termLoading.value = true; listContextTerms(termQuery).then((res) => { terms.value = res.data; termLoading.value = false; }); }
function getList() { loading.value = true; listConcept(query).then((res) => { list.value = res.rows; total.value = res.total; loading.value = false; }); }
function doMerge() {
  const aliases = termSel.value.map((x) => x.term);
  const name = mergeName.value || aliases[0];
  mergeConcept({ conceptType: termQuery.contextType, name, aliases }).then((res) => {
    proxy.$modal.msgSuccess(`已归并，回填 ${res.data.mapped} 条实体`); mergeName.value = ""; loadTerms(); getList();
  });
}
function openEdit(row) {
  form.value = row ? { id: row.id, conceptType: row.conceptType, name: row.name } : { conceptType: termQuery.contextType, name: "" };
  synText.value = row ? (row.synonyms || []).join(",") : ""; editOpen.value = true;
}
function submit() {
  const synonyms = synText.value ? synText.value.split(/[,，;；]/).map((x) => x.trim()).filter(Boolean) : [];
  saveConcept({ ...form.value, synonyms }).then(() => { proxy.$modal.msgSuccess("保存成功"); editOpen.value = false; getList(); });
}
function remove(row) {
  proxy.$modal.confirm(`删除术语“${row.name}”？其实体映射将被清空`).then(() => delConcept(row.id)).then(() => { proxy.$modal.msgSuccess("已删除"); getList(); loadTerms(); });
}
loadTerms(); getList();
</script>

<style scoped>
.merge-bar { margin-top: 10px; display: flex; gap: 10px; align-items: center; }
</style>
