<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  FolderOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import type { ProjectMemberRow, ProjectParticipation, ProjectRow } from '@/api/projects'
import {
  fetchProjectList,
  fetchProjectMembers,
  addProjectMember,
  removeProjectMember,
  createProject,
  updateProject,
  deleteProject,
} from '@/api/projects'

const participationOptions: { value: ProjectParticipation; label: string }[] = [
  { value: 'all', label: '全部（我创建或我加入）' },
  { value: 'owned', label: '仅我负责' },
  { value: 'joined', label: '仅我加入（非负责人）' },
]

const list = ref<ProjectRow[]>([])
const loading = ref(false)

const filters = reactive({
  participation: 'all' as ProjectParticipation,
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

function formatTime(v: string | null) {
  if (!v) return '-'
  try {
    return new Date(v).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return v
  }
}

function roleLabel(role: string) {
  const m: Record<string, string> = {
    owner: '负责人',
    leader: '组长',
    tester: '测试',
  }
  return m[role] ?? role
}

function roleColor(role: string) {
  if (role === 'owner') return 'blue'
  if (role === 'leader') return 'purple'
  if (role === 'tester') return 'cyan'
  return 'default'
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await fetchProjectList({
      page: pagination.current,
      size: pagination.pageSize,
      participation: filters.participation,
    })
    if (res.code === 200 || res.code === 0) {
      const d = res.data!
      list.value = d.items
      pagination.total = d.total
    }
  } catch {
    /* 提示由 request 拦截器 */
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.current = 1
  void loadData()
}

const handlePaginationChange = (page: number, pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = page
  void loadData()
}

const modalOpen = ref(false)
const modalSaving = ref(false)
const editingId = ref<number | null>(null)
const formState = reactive({
  name: '',
  description: '' as string,
})

function openCreate() {
  editingId.value = null
  formState.name = ''
  formState.description = ''
  modalOpen.value = true
}

function openEdit(row: ProjectRow) {
  editingId.value = row.id
  formState.name = row.name
  formState.description = row.description ?? ''
  modalOpen.value = true
}

async function submitModal() {
  const name = formState.name.trim()
  if (!name) {
    message.warning('请输入项目名称')
    return
  }
  modalSaving.value = true
  try {
    const desc = formState.description.trim()
    if (editingId.value == null) {
      await createProject({
        name,
        description: desc || null,
      })
      message.success('已创建项目')
    } else {
      await updateProject(editingId.value, {
        name,
        description: desc || null,
      })
      message.success('已保存')
    }
    modalOpen.value = false
    await loadData()
  } catch {
    /* 拦截器 */
  } finally {
    modalSaving.value = false
  }
}

function confirmDelete(row: ProjectRow) {
  Modal.confirm({
    title: '确认删除该项目？',
    content: `将软删除「${row.name}」，成员与后续业务数据请遵循后端策略。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      await deleteProject(row.id)
      message.success('已删除')
      await loadData()
    },
  })
}

const isOwner = (row: ProjectRow) => row.my_role === 'owner'

/** 成员管理弹窗 */
const membersModalOpen = ref(false)
const membersLoading = ref(false)
const membersList = ref<ProjectMemberRow[]>([])
const membersContext = ref<ProjectRow | null>(null)
const addMemberUsername = ref('')
const addMemberRole = ref<'leader' | 'tester'>('tester')
const addMemberSubmitting = ref(false)

function openMembersModal(row: ProjectRow) {
  membersContext.value = row
  addMemberUsername.value = ''
  addMemberRole.value = 'tester'
  membersModalOpen.value = true
  void loadMembers()
}

async function loadMembers() {
  const pid = membersContext.value?.id
  if (pid == null) return
  membersLoading.value = true
  try {
    const res = await fetchProjectMembers(pid)
    if (res.code === 200 || res.code === 0) {
      membersList.value = res.data?.items ?? []
    }
  } catch {
    membersList.value = []
  } finally {
    membersLoading.value = false
  }
}

async function submitAddMember() {
  const ctx = membersContext.value
  const u = addMemberUsername.value.trim()
  if (!ctx || !u) {
    message.warning('请输入要添加的用户名')
    return
  }
  addMemberSubmitting.value = true
  try {
    await addProjectMember(ctx.id, { username: u, role: addMemberRole.value })
    message.success('已添加成员')
    addMemberUsername.value = ''
    await loadMembers()
    await loadData()
  } catch {
    /* 拦截器 */
  } finally {
    addMemberSubmitting.value = false
  }
}

function confirmRemoveMember(m: ProjectMemberRow) {
  const ctx = membersContext.value
  if (!ctx) return
  if (m.role === 'owner') {
    message.warning('不能移除负责人')
    return
  }
  Modal.confirm({
    title: '确认移除该成员？',
    content: `将「${m.nickname || m.username}」从项目中移除。`,
    okText: '移除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      await removeProjectMember(ctx.id, m.user_id)
      message.success('已移除')
      await loadMembers()
      await loadData()
    },
  })
}

const memberColumns = [
  { title: '用户名', dataIndex: 'username', key: 'username', width: 140, ellipsis: true },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname', width: 120, ellipsis: true },
  { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
  { title: '操作', dataIndex: 'action', key: 'action', width: 100 },
]

onMounted(() => {
  void loadData()
})
</script>

<template>
  <div class="projects-page">
    <div class="projects-page__head">
      <div>
        <h1 class="projects-page__title">我的项目</h1>
        <p class="projects-page__desc">
          管理测试用例归属的项目。可按参与方式筛选；负责人可编辑、删除项目，并通过「成员」添加组长或测试成员（输入对方登录用户名）。
        </p>
      </div>
      <div class="projects-page__actions">
        <a-select
          v-model:value="filters.participation"
          :options="participationOptions"
          class="projects-page__filter"
          @change="handleFilterChange"
        />
        <a-button type="primary" @click="openCreate">
          <template #icon>
            <PlusOutlined />
          </template>
          新建项目
        </a-button>
      </div>
    </div>

    <a-spin class="projects-page__spin" :spinning="loading">
      <div v-if="!list.length && !loading" class="projects-page__empty">
        <AppstoreOutlined class="projects-page__empty-icon" />
        <p>暂无项目，请点击「新建项目」</p>
      </div>

      <template v-else>
        <a-row :gutter="[16, 16]">
          <a-col
            v-for="row in list"
            :key="row.id"
            :xs="24"
            :sm="24"
            :md="12"
            :lg="8"
            :xl="6"
            :xxl="6"
          >
            <div class="projects-card">
              <div class="projects-card__head">
                <div class="projects-card__brand">
                  <div class="projects-card__logo-wrap">
                    <FolderOutlined class="projects-card__folder-icon" />
                  </div>
                  <div class="projects-card__titles">
                    <div class="projects-card__name" :title="row.name">{{ row.name }}</div>
                    <div class="projects-card__sub" :title="row.description || undefined">
                      {{ row.description || '暂无描述' }}
                    </div>
                  </div>
                </div>
                <a-tag :color="roleColor(row.my_role)">{{ roleLabel(row.my_role) }}</a-tag>
              </div>

              <div class="projects-card__body">
                <div class="projects-card__row">
                  <span class="projects-card__k">负责人</span>
                  <span class="projects-card__v">{{ row.owner_name || '—' }}</span>
                </div>
                <div class="projects-card__row projects-card__row--wrap">
                  <span class="projects-card__k">更新时间</span>
                  <span class="projects-card__v">{{ formatTime(row.updated_at) }}</span>
                </div>
              </div>

              <div class="projects-card__foot">
                <a-button type="link" size="small" @click="openMembersModal(row)">
                  <TeamOutlined /> 成员
                </a-button>
                <template v-if="isOwner(row)">
                  <a-button type="link" size="small" @click="openEdit(row)">
                    <EditOutlined /> 编辑
                  </a-button>
                  <a-button type="link" size="small" danger @click="confirmDelete(row)">
                    <DeleteOutlined /> 删除
                  </a-button>
                </template>
              </div>
            </div>
          </a-col>
        </a-row>

        <div v-if="pagination.total > 0" class="projects-page__pager">
          <a-pagination
            v-model:current="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :show-size-changer="true"
            :show-total="(t: number) => `共 ${t} 条`"
            @change="handlePaginationChange"
          />
        </div>
      </template>
    </a-spin>

    <a-modal
      v-model:open="modalOpen"
      :title="editingId == null ? '新建项目' : '编辑项目'"
      width="560px"
      :confirm-loading="modalSaving"
      :mask-closable="false"
      destroy-on-close
      :footer="null"
      @cancel="modalOpen = false"
    >
      <a-form layout="vertical" class="projects-modal-form">
        <a-form-item label="项目名称" required>
          <a-input
            v-model:value="formState.name"
            placeholder="请输入项目名称"
            size="large"
            :maxlength="50"
            show-count
          />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea
            v-model:value="formState.description"
            placeholder="可选"
            size="large"
            :rows="4"
            :maxlength="200"
            show-count
          />
        </a-form-item>
      </a-form>

      <div class="projects-modal__footer">
        <a-button @click="modalOpen = false">取消</a-button>
        <a-button type="primary" :loading="modalSaving" @click="submitModal">保存</a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="membersModalOpen"
      :title="membersContext ? `成员 — ${membersContext.name}` : '成员'"
      width="720px"
      :footer="null"
      :mask-closable="false"
      destroy-on-close
      @cancel="membersModalOpen = false"
    >
      <a-spin :spinning="membersLoading">
        <a-table
          :columns="memberColumns"
          :data-source="membersList"
          :pagination="false"
          size="small"
          row-key="user_id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'nickname'">
              {{ (record as ProjectMemberRow).nickname || '—' }}
            </template>
            <template v-else-if="column.dataIndex === 'role'">
              <a-tag :color="roleColor((record as ProjectMemberRow).role)">
                {{ roleLabel((record as ProjectMemberRow).role) }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button
                v-if="membersContext && isOwner(membersContext) && (record as ProjectMemberRow).role !== 'owner'"
                type="link"
                size="small"
                danger
                @click="confirmRemoveMember(record as ProjectMemberRow)"
              >
                移除
              </a-button>
              <span v-else class="projects-card__foot-hint">—</span>
            </template>
          </template>
        </a-table>

        <div v-if="membersContext && isOwner(membersContext)" class="members-add">
          <div class="members-add__title">添加成员</div>
          <a-space wrap :size="12" class="members-add__row">
            <a-input
              v-model:value="addMemberUsername"
              placeholder="对方登录用户名"
              style="width: 200px"
              allow-clear
              @pressEnter="submitAddMember"
            />
            <a-select v-model:value="addMemberRole" style="width: 120px">
              <a-select-option value="leader">组长</a-select-option>
              <a-select-option value="tester">测试</a-select-option>
            </a-select>
            <a-button type="primary" :loading="addMemberSubmitting" @click="submitAddMember">
              添加
            </a-button>
          </a-space>
          <p class="members-add__hint">被添加用户须已注册；负责人不可通过此处重复添加。</p>
        </div>
      </a-spin>

      <div class="projects-modal__footer">
        <a-button @click="membersModalOpen = false">关闭</a-button>
      </div>
    </a-modal>
  </div>
</template>

<style lang="scss" scoped>
/* 与 views/llm/index.vue 页级布局对齐 */
.projects-page {
  width: 100%;
  max-width: none;
  box-sizing: border-box;
  padding: 16px 16px 32px;
  min-width: 0;
}

.projects-page__spin {
  display: block;
  min-width: 0;

  :deep(.ant-spin-container) {
    min-width: 0;
  }
}

.projects-page__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.projects-page__title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.projects-page__desc {
  margin: 0;
  max-width: none;
  font-size: 13px;
  line-height: 1.6;
  color: #8c8c8c;
}

.projects-page__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.projects-page__filter {
  min-width: 240px;
}

.projects-page__empty {
  text-align: center;
  padding: 48px 16px;
  color: #bfbfbf;
  background: #fafafa;
  border-radius: 12px;
  border: 1px dashed #e8e8e8;
}

.projects-page__empty-icon {
  font-size: 40px;
  margin-bottom: 8px;
  display: block;
}

.projects-page__pager {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.projects-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  }
}

.projects-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 14px;
}

.projects-card__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.projects-card__logo-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #f5f5f5;
  overflow: hidden;
}

.projects-card__folder-icon {
  font-size: 20px;
  color: #1890ff;
}

.projects-card__titles {
  min-width: 0;
}

.projects-card__name {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.projects-card__sub {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.45;
  max-width: 100%;
}

.projects-card__body {
  flex: 1;
  font-size: 12px;
  color: #595959;
}

.projects-card__row {
  display: grid;
  grid-template-columns: 72px 1fr;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  &--wrap {
    align-items: start;

    .projects-card__v {
      white-space: normal;
      word-break: break-all;
      line-height: 1.45;
    }
  }
}

.projects-card__k {
  color: #8c8c8c;
}

.projects-card__v {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &--mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 11px;
  }
}

.projects-card__foot {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 2px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f5f5f5;

  :deep(.ant-btn) {
    padding: 0 6px;
  }
}

.projects-card__foot-hint {
  font-size: 12px;
  color: #bfbfbf;
}

.projects-modal-form {
  margin-bottom: 8px;
}

.projects-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  margin-top: 8px;
}

.members-add {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.members-add__title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 10px;
}

.members-add__row {
  width: 100%;
}

.members-add__hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.5;
}
</style>
