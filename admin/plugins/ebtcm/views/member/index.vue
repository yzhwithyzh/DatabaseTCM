<template>
  <div class="app-container">
    <el-tabs v-model="tab" @tab-change="onTab">
      <el-tab-pane v-for="t in TABS" :key="t.value" :name="t.value">
        <template #label>
          {{ t.label }}
          <el-badge v-if="t.value === 'pending' && counts.pending" :value="counts.pending" class="tab-badge" />
          <span v-else-if="t.value && counts[t.value]" class="tab-count">{{ counts[t.value] }}</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <el-form :model="query" :inline="true">
      <el-form-item label="关键词">
        <el-input v-model="query.keyword" placeholder="用户名 / 姓名 / 单位 / 手机 / 邮箱" clearable style="width: 260px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="来源">
        <el-select v-model="query.source" clearable placeholder="全部" style="width: 120px">
          <el-option label="自助注册" value="register" /><el-option label="后台创建" value="admin" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5"><el-button type="primary" plain icon="Plus" @click="openEdit()" v-hasPermi="['ebtcm:member:edit']">新增用户</el-button></el-col>
      <el-col :span="1.5"><el-button type="success" plain icon="Check" :disabled="!pendingSel.length" @click="openAudit(pendingSel, true)" v-hasPermi="['ebtcm:member:audit']">批量通过</el-button></el-col>
      <el-col :span="1.5"><el-button type="warning" plain icon="Close" :disabled="!pendingSel.length" @click="openAudit(pendingSel, false)" v-hasPermi="['ebtcm:member:audit']">批量驳回</el-button></el-col>
      <el-col :span="1.5"><el-button type="danger" plain icon="Delete" :disabled="!sel.length" @click="remove(sel)" v-hasPermi="['ebtcm:member:remove']">删除</el-button></el-col>
    </el-row>

    <el-table v-loading="loading" :data="list" @selection-change="(v) => (sel = v)">
      <el-table-column type="selection" width="45" />
      <el-table-column label="用户名" prop="userName" min-width="120" show-overflow-tooltip />
      <el-table-column label="姓名" prop="realName" width="100" />
      <el-table-column label="单位 / 部门" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ [row.organization, row.department].filter(Boolean).join(" / ") || "-" }}</template>
      </el-table-column>
      <el-table-column label="职称/身份" prop="jobTitle" width="100" show-overflow-tooltip />
      <el-table-column label="联系方式" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ [row.phone, row.email].filter(Boolean).join(" / ") || "-" }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><el-tag :type="MEMBER_STATUS_TAG[row.status]" size="small">{{ MEMBER_STATUS[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column label="来源" width="85"><template #default="{ row }">{{ row.source === "admin" ? "后台创建" : "自助注册" }}</template></el-table-column>
      <el-table-column label="有效期至" width="105">
        <template #default="{ row }"><span :class="{ expired: isExpired(row) }">{{ row.expireDate || "长期" }}</span></template>
      </el-table-column>
      <el-table-column label="申请/创建时间" width="160"><template #default="{ row }">{{ fmt(row.createTime) }}</template></el-table-column>
      <el-table-column label="最近登录" width="160"><template #default="{ row }">{{ fmt(row.lastLoginTime) || "-" }}</template></el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button link type="success" icon="Check" @click="openAudit([row], true)" v-hasPermi="['ebtcm:member:audit']">通过</el-button>
            <el-button link type="warning" icon="Close" @click="openAudit([row], false)" v-hasPermi="['ebtcm:member:audit']">驳回</el-button>
          </template>
          <el-button v-if="row.status === 'active'" link type="warning" icon="Lock" @click="setStatus(row, 'disabled')" v-hasPermi="['ebtcm:member:edit']">停用</el-button>
          <el-button v-if="row.status === 'disabled'" link type="success" icon="Unlock" @click="setStatus(row, 'active')" v-hasPermi="['ebtcm:member:edit']">启用</el-button>
          <el-button link type="primary" icon="Edit" @click="openEdit(row)" v-hasPermi="['ebtcm:member:edit']">详情</el-button>
          <el-dropdown v-hasPermi="['ebtcm:member:edit']" @command="(c) => c === 'pwd' ? openPwd(row) : remove([row])">
            <el-button link type="primary" icon="DArrowRight">更多</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="pwd" icon="Key">重置密码</el-dropdown-item>
                <el-dropdown-item command="del" icon="Delete">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />

    <!-- 新增 / 详情编辑 -->
    <el-dialog :title="form.memberId ? '用户详情' : '新增用户'" v-model="editOpen" width="620px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row>
          <el-col :span="12"><el-form-item label="用户名" prop="userName"><el-input v-model="form.userName" :disabled="!!form.memberId" /></el-form-item></el-col>
          <el-col :span="12" v-if="!form.memberId"><el-form-item label="初始密码" prop="password"><el-input v-model="form.password" type="password" show-password placeholder="8 位以上，含字母和数字" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="姓名" prop="realName"><el-input v-model="form.realName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="职称/身份"><el-input v-model="form.jobTitle" placeholder="如 主治医师 / 研究生" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="单位"><el-input v-model="form.organization" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="部门/科室"><el-input v-model="form.department" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机"><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item label="有效期至">
              <el-date-picker v-model="form.expireDate" type="date" value-format="YYYY-MM-DD" placeholder="留空为长期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="!form.memberId || ['active', 'disabled'].includes(form.status)">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status"><el-radio value="active">正常</el-radio><el-radio value="disabled">停用</el-radio></el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
        <template v-if="form.memberId">
          <el-divider content-position="left">申请与审核</el-divider>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="状态"><el-tag :type="MEMBER_STATUS_TAG[form.status]" size="small">{{ MEMBER_STATUS[form.status] }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="来源">{{ form.source === "admin" ? `后台创建（${form.createBy || "-"}）` : "自助注册" }}</el-descriptions-item>
            <el-descriptions-item label="申请理由" :span="2">{{ form.applyReason || "-" }}</el-descriptions-item>
            <el-descriptions-item label="审核人">{{ form.auditBy || "-" }}</el-descriptions-item>
            <el-descriptions-item label="审核时间">{{ fmt(form.auditTime) || "-" }}</el-descriptions-item>
            <el-descriptions-item label="审核意见" :span="2">{{ form.auditRemark || "-" }}</el-descriptions-item>
            <el-descriptions-item label="最近登录">{{ fmt(form.lastLoginTime) || "-" }}</el-descriptions-item>
            <el-descriptions-item label="登录 IP">{{ form.lastLoginIp || "-" }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审核 -->
    <el-dialog :title="audit.approved ? '通过注册申请' : '驳回注册申请'" v-model="auditOpen" width="480px" append-to-body>
      <p class="audit-who">{{ audit.names }}</p>
      <el-form label-width="80px">
        <el-form-item v-if="audit.approved" label="有效期至">
          <el-date-picker v-model="audit.expireDate" type="date" value-format="YYYY-MM-DD" placeholder="留空为长期" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="audit.approved ? '审核意见' : '驳回原因'" :required="!audit.approved">
          <el-input v-model="audit.auditRemark" type="textarea" :rows="3" :placeholder="audit.approved ? '选填' : '必填，用户登录时会看到'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditOpen = false">取消</el-button>
        <el-button :type="audit.approved ? 'success' : 'warning'" @click="submitAudit">{{ audit.approved ? "通过" : "驳回" }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="EbtcmMember">
import {
  listMember, getMemberCounts, saveMember, auditMember, changeMemberStatus, resetMemberPwd, delMember, MEMBER_STATUS, MEMBER_STATUS_TAG,
} from "~/plugins/ebtcm/api/ebtcm";

const { proxy } = getCurrentInstance();
const TABS = [
  { label: "全部", value: "" }, { label: "待审核", value: "pending" }, { label: "正常", value: "active" },
  { label: "已驳回", value: "rejected" }, { label: "已停用", value: "disabled" },
];
const tab = ref("");
const query = reactive({ pageNum: 1, pageSize: 10, keyword: undefined, source: undefined, status: undefined });
const list = ref([]); const total = ref(0); const loading = ref(false); const sel = ref([]); const counts = ref({});
const pendingSel = computed(() => sel.value.filter((x) => x.status === "pending"));

const editOpen = ref(false); const form = ref({});
const rules = {
  userName: [{ required: true, message: "请输入用户名", trigger: "blur" }, { pattern: /^[A-Za-z0-9_@.\-]{4,50}$/, message: "4-50 位字母、数字或 _ @ . -", trigger: "blur" }],
  password: [{ required: true, message: "请输入初始密码", trigger: "blur" }, { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, message: "8-32 位，且同时包含字母和数字", trigger: "blur" }],
  realName: [{ required: true, message: "请输入姓名", trigger: "blur" }],
};
const auditOpen = ref(false); const audit = ref({});

const fmt = (t) => (t ? String(t).replace("T", " ").slice(0, 16) : "");
const isExpired = (row) => row.expireDate && row.expireDate < new Date().toISOString().slice(0, 10);

function getList() {
  loading.value = true;
  listMember(query).then((res) => { list.value = res.rows; total.value = res.total; loading.value = false; });
  getMemberCounts().then((res) => { counts.value = res.data || {}; });
}
function onTab(v) { query.status = v || undefined; query.pageNum = 1; getList(); }
function handleQuery() { query.pageNum = 1; getList(); }
function resetQuery() { query.keyword = undefined; query.source = undefined; handleQuery(); }

function openEdit(row) {
  form.value = row ? { ...row } : { status: "active" };
  editOpen.value = true;
  nextTick(() => proxy.$refs.formRef?.clearValidate());
}
function submit() {
  proxy.$refs.formRef.validate((ok) => {
    if (!ok) return;
    const f = form.value;
    const data = {
      memberId: f.memberId, userName: f.memberId ? undefined : f.userName, password: f.memberId ? undefined : f.password,
      realName: f.realName, organization: f.organization, department: f.department, jobTitle: f.jobTitle,
      phone: f.phone, email: f.email, expireDate: f.expireDate || null, remark: f.remark, status: f.status,
    };
    saveMember(data).then(() => { proxy.$modal.msgSuccess("保存成功"); editOpen.value = false; getList(); });
  });
}

function openAudit(rows, approved) {
  audit.value = { approved, ids: rows.map((r) => r.memberId), names: rows.map((r) => `${r.realName}（${r.userName}）`).join("、"), auditRemark: "", expireDate: null };
  auditOpen.value = true;
}
function submitAudit() {
  const a = audit.value;
  if (!a.approved && !a.auditRemark.trim()) return proxy.$modal.msgWarning("请填写驳回原因");
  auditMember({ memberIds: a.ids, approved: a.approved, auditRemark: a.auditRemark || null, expireDate: a.expireDate || null }).then((res) => {
    proxy.$modal.msgSuccess(res.msg); auditOpen.value = false; getList();
  });
}

function setStatus(row, status) {
  const act = status === "active" ? "启用" : "停用";
  proxy.$modal.confirm(`确认${act}账号“${row.realName}（${row.userName}）”？${status === "disabled" ? "停用后该用户会立即被退出登录。" : ""}`)
    .then(() => changeMemberStatus({ memberIds: [row.memberId], status }))
    .then((res) => { proxy.$modal.msgSuccess(res.msg); getList(); });
}
function openPwd(row) {
  proxy.$prompt(`为“${row.realName}（${row.userName}）”设置新密码`, "重置密码", {
    inputType: "password", inputPattern: /^(?=.*[A-Za-z])(?=.*\d).{8,32}$/, inputErrorMessage: "8-32 位，且同时包含字母和数字",
  }).then(({ value }) => resetMemberPwd({ memberId: row.memberId, password: value }))
    .then(() => proxy.$modal.msgSuccess("密码已重置"));
}
function remove(rows) {
  proxy.$modal.confirm(`删除 ${rows.map((r) => r.userName).join("、")}？删除后不可恢复。`)
    .then(() => delMember(rows.map((r) => r.memberId).join(",")))
    .then((res) => { proxy.$modal.msgSuccess(res.msg); getList(); });
}

getList();
</script>

<style scoped>
.tab-badge { margin-left: 4px; vertical-align: 1px; }
.tab-count { margin-left: 4px; color: var(--el-text-color-secondary); font-size: 12px; }
.expired { color: var(--el-color-danger); }
.audit-who { margin: 0 0 14px; color: var(--el-text-color-regular); }
</style>
