<script setup lang="ts">
import {
  DeleteOutlined,
  EditOutlined,
  FolderOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import { computed, reactive, ref, watch } from 'vue'
import { Empty, message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import {
  collectModuleSubtreeIds,
  collectTreeKeys,
  createProjectModule,
  deleteProjectModule,
  fetchProjectModuleTree,
  projectModuleRootsToAntTreeData,
  projectModuleRootsToTreeSelectData,
  projectModuleRootsToTreeSelectDataExcluding,
  updateProjectModule,
  type ProjectModuleAntTreeNode,
  type ProjectModuleNode,
} from '@/api/project-modules'

const props = withDefaults(
  defineProps<{
    /** 项目主键，<=0 时不请求 */
    projectId: number
    /** 当前选中的模块 id */
    modelValue?: number | null
    /** 面板标题 */
    title?: string
    /** 是否显示「新增模块」 */
    showCreate?: boolean
    /** 是否在树节点右侧显示编辑 / 删除 */
    showRowActions?: boolean
    /** 是否显示刷新按钮 */
    showRefresh?: boolean
    /** 加载完成后是否展开全部节点 */
    autoExpandAll?: boolean
  }>(),
  {
    modelValue: null,
    title: '模块目录',
    showCreate: true,
    showRowActions: true,
    showRefresh: true,
    autoExpandAll: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  /** 选中叶子或任意节点时抛出完整节点数据，便于右侧列表拉取用例 */
  select: [node: ProjectModuleNode]
  /** 树数据加载完成（含 roots 为空） */
  loaded: [roots: ProjectModuleNode[]]
}>()

const loading = ref(false)
const loadError = ref<string | null>(null)
const treeData = ref<ProjectModuleAntTreeNode[]>([])
const keyToModule = ref<Map<string, ProjectModuleNode>>(new Map())
const expandedKeys = ref<(string | number)[]>([])
/** 最近一次加载成功的树，用于上级模块下拉 */
const lastRoots = ref<ProjectModuleNode[]>([])

const emptySimpleImage = Empty.PRESENTED_IMAGE_SIMPLE

const createOpen = ref(false)
const createSubmitting = ref(false)
const formRef = ref<FormInstance>()
const createForm = reactive({
  name: '',
  parent_id: undefined as number | undefined,
  description: '',
})

const createRules = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { max: 200, message: '不超过 200 字', trigger: 'blur' },
  ],
}

const parentTreeSelectData = computed(() => projectModuleRootsToTreeSelectData(lastRoots.value))

const editingModuleId = ref<number | null>(null)
const editOpen = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  name: '',
  parent_id: undefined as number | undefined,
  description: '',
})

const editRules = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { max: 200, message: '不超过 200 字', trigger: 'blur' },
  ],
}

const editParentTreeSelectData = computed(() => {
  const mid = editingModuleId.value
  if (mid == null) return []
  const exclude = collectModuleSubtreeIds(lastRoots.value, mid)
  return projectModuleRootsToTreeSelectDataExcluding(lastRoots.value, exclude)
})

const selectedKeys = computed(() =>
  props.modelValue != null && Number.isFinite(props.modelValue)
    ? [String(props.modelValue)]
    : [],
)

async function load() {
  loadError.value = null
  if (!props.projectId || props.projectId <= 0) {
    treeData.value = []
    keyToModule.value = new Map()
    expandedKeys.value = []
    lastRoots.value = []
    emit('loaded', [])
    return
  }

  loading.value = true
  try {
    const res = await fetchProjectModuleTree(props.projectId)
    if (res.code !== 200 && res.code !== 0) {
      loadError.value = res.message || '加载模块树失败'
      treeData.value = []
      keyToModule.value = new Map()
      expandedKeys.value = []
      lastRoots.value = []
      emit('loaded', [])
      return
    }
    const roots = res.data?.roots ?? []
    lastRoots.value = roots
    const { treeData: nodes, keyToModule: map } = projectModuleRootsToAntTreeData(roots)
    treeData.value = nodes
    keyToModule.value = map
    expandedKeys.value = props.autoExpandAll ? collectTreeKeys(nodes) : nodes.map((n) => n.key)
    emit('loaded', roots)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载模块树失败'
    loadError.value = msg
    treeData.value = []
    keyToModule.value = new Map()
    expandedKeys.value = []
    lastRoots.value = []
    emit('loaded', [])
  } finally {
    loading.value = false
  }
}

function onTreeSelect(keys: (string | number)[]) {
  const raw = keys[0]
  if (raw === undefined) {
    emit('update:modelValue', null)
    return
  }
  const key = String(raw)
  const id = Number(key)
  emit('update:modelValue', id)
  const node = keyToModule.value.get(key)
  if (node) {
    emit('select', node)
  }
}

function openCreateModal() {
  createForm.name = ''
  createForm.description = ''
  createForm.parent_id = props.modelValue ?? undefined
  createOpen.value = true
}

function openCreateModalRoot() {
  createForm.name = ''
  createForm.description = ''
  createForm.parent_id = undefined
  createOpen.value = true
}

async function handleCreateOk() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  const name = createForm.name.trim()
  if (!name) {
    return
  }
  const descRaw = createForm.description.trim()
  createSubmitting.value = true
  try {
    const res = await createProjectModule(props.projectId, {
      name,
      parent_id: createForm.parent_id ?? null,
      description: descRaw ? descRaw : null,
    })
    if (res.code !== 200 && res.code !== 0) {
      return
    }
    const raw = res.data
    if (!raw) {
      return
    }
    const node: ProjectModuleNode = {
      ...raw,
      children: raw.children ?? [],
    }
    message.success('模块已创建')
    createOpen.value = false
    await load()
    emit('update:modelValue', node.id)
    emit('select', node)
  } finally {
    createSubmitting.value = false
  }
}

function openEditForKey(key: string | number) {
  const node = keyToModule.value.get(String(key))
  if (!node) return
  editingModuleId.value = node.id
  editForm.name = node.name
  editForm.parent_id = node.parent_id ?? undefined
  editForm.description = node.description ?? ''
  editOpen.value = true
}

async function handleEditOk() {
  try {
    await editFormRef.value?.validate()
  } catch {
    return
  }
  const mid = editingModuleId.value
  if (mid == null) return
  const name = editForm.name.trim()
  if (!name) return
  const descRaw = editForm.description.trim()
  editSubmitting.value = true
  try {
    const res = await updateProjectModule(props.projectId, mid, {
      name,
      parent_id: editForm.parent_id ?? null,
      description: descRaw ? descRaw : null,
    })
    if (res.code !== 200 && res.code !== 0) {
      return
    }
    const raw = res.data
    if (!raw) {
      return
    }
    const node: ProjectModuleNode = {
      ...raw,
      children: raw.children ?? [],
    }
    message.success('已保存')
    editOpen.value = false
    await load()
    emit('update:modelValue', node.id)
    emit('select', node)
  } finally {
    editSubmitting.value = false
  }
}

async function confirmDeleteModule(key: string | number) {
  const node = keyToModule.value.get(String(key))
  if (!node) return
  const subtree = collectModuleSubtreeIds(lastRoots.value, node.id)
  const sel = props.modelValue
  try {
    const res = await deleteProjectModule(props.projectId, node.id)
    if (res.code !== 200 && res.code !== 0) {
      return
    }
    message.success('已删除')
    if (sel != null && subtree.has(sel)) {
      emit('update:modelValue', null)
    }
    await load()
  } catch {
    /* 全局拦截器已提示 */
  }
}

watch(editOpen, (open) => {
  if (!open) {
    editingModuleId.value = null
  }
})

watch(
  () => props.projectId,
  () => {
    void load()
  },
  { immediate: true },
)

defineExpose({
  reload: load,
})
</script>

<template>
  <div class="pmtp">
    <div class="pmtp__header">
      <span class="pmtp__title">{{ title }}</span>
      <div class="pmtp__actions">
        <a-button
          v-if="showCreate"
          type="text"
          size="small"
          class="pmtp__add pmtp__toolbar-text"
          :disabled="loading || projectId <= 0"
          @click="openCreateModal"
        >
          <PlusOutlined />
          新增
        </a-button>
        <a-button
          v-if="showRefresh"
          type="text"
          size="small"
          class="pmtp__toolbar-text"
          :disabled="loading || projectId <= 0"
          aria-label="刷新模块树"
          @click="load()"
        >
          <ReloadOutlined />
        </a-button>
      </div>
    </div>

    <a-modal
      v-model:open="createOpen"
      title="新增模块"
      ok-text="创建"
      cancel-text="取消"
      :confirm-loading="createSubmitting"
      :destroy-on-close="true"
      width="440px"
      @ok="handleCreateOk"
    >
      <a-form
        ref="formRef"
        layout="vertical"
        class="pmtp-create-form"
        :model="createForm"
        :rules="createRules"
      >
        <a-form-item label="模块名称" name="name">
          <a-input v-model:value="createForm.name" placeholder="同级目录下名称唯一" allow-clear />
        </a-form-item>
        <a-form-item label="上级模块" name="parent_id">
          <a-tree-select
            v-model:value="createForm.parent_id"
            allow-clear
            show-search
            tree-default-expand-all
            placeholder="不选则为根目录"
            :disabled="!parentTreeSelectData.length"
            :tree-data="parentTreeSelectData"
            tree-node-filter-prop="title"
          />
        </a-form-item>
        <a-form-item label="说明" name="description">
          <a-textarea
            v-model:value="createForm.description"
            placeholder="可选"
            :rows="2"
            :maxlength="2000"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="editOpen"
      title="编辑模块"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="editSubmitting"
      :destroy-on-close="true"
      width="440px"
      @ok="handleEditOk"
    >
      <a-form
        ref="editFormRef"
        layout="vertical"
        class="pmtp-create-form"
        :model="editForm"
        :rules="editRules"
      >
        <a-form-item label="模块名称" name="name">
          <a-input v-model:value="editForm.name" placeholder="同级目录下名称唯一" allow-clear />
        </a-form-item>
        <a-form-item label="上级模块" name="parent_id">
          <a-tree-select
            v-model:value="editForm.parent_id"
            allow-clear
            show-search
            tree-default-expand-all
            placeholder="不选则为根目录"
            :tree-data="editParentTreeSelectData"
            tree-node-filter-prop="title"
          />
        </a-form-item>
        <a-form-item label="说明" name="description">
          <a-textarea
            v-model:value="editForm.description"
            placeholder="可选"
            :rows="2"
            :maxlength="2000"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-spin :spinning="loading" class="pmtp__spin">
      <a-alert
        v-if="loadError"
        type="error"
        show-icon
        :message="loadError"
        class="pmtp__alert"
      />

      <div v-else-if="!treeData.length" class="pmtp__empty">
        <a-empty description="暂无模块" :image="emptySimpleImage">
          <template v-if="showCreate" #extra>
            <a-button
              type="text"
              size="small"
              class="pmtp__add pmtp__toolbar-text"
              :disabled="projectId <= 0"
              @click="openCreateModalRoot"
            >
              <PlusOutlined />
              新增模块
            </a-button>
          </template>
        </a-empty>
        <p class="pmtp__empty-hint">
          负责人或测试负责人可新增模块；目录树可在功能 / 接口 / UI 用例等页面复用。
        </p>
      </div>

      <a-tree
        v-else
        class="pmtp-tree"
        block-node
        :tree-data="treeData"
        v-model:expanded-keys="expandedKeys"
        :selected-keys="selectedKeys"
        @select="onTreeSelect"
      >
        <template #title="{ key, title: text }">
          <div class="pmtp-tree__title-wrap">
            <span class="pmtp-tree__row">
              <FolderOutlined class="pmtp-tree__icon" aria-hidden="true" />
              <span class="pmtp-tree__text" :title="String(text)">{{ text }}</span>
            </span>
            <span v-if="showRowActions" class="pmtp-tree__actions" @click.stop>
              <a-button
                type="text"
                size="small"
                class="pmtp-tree__action-btn pmtp__toolbar-text"
                aria-label="编辑模块"
                @click.stop="openEditForKey(key)"
              >
                <EditOutlined />
              </a-button>
              <a-popconfirm
                title="删除该模块？"
                description="将同时删除其下所有子模块（软删除）。"
                ok-text="删除"
                cancel-text="取消"
                ok-type="danger"
                @confirm="confirmDeleteModule(key)"
              >
                <a-button
                  type="text"
                  size="small"
                  danger
                  class="pmtp-tree__action-btn"
                  aria-label="删除模块"
                  @click.stop
                >
                  <DeleteOutlined />
                </a-button>
              </a-popconfirm>
            </span>
          </div>
        </template>
      </a-tree>
    </a-spin>
  </div>
</template>

<style lang="scss" scoped>
.pmtp {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.pmtp__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.pmtp__title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.pmtp__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.pmtp__add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pmtp__toolbar-text {
  color: rgba(0, 0, 0, 0.45) !important;

  &:hover {
    color: #1890ff !important;
  }
}

.pmtp__spin {
  flex: 1;
  min-height: 200px;
  padding: 8px 8px 12px;
}

.pmtp__alert {
  margin: 8px;
}

.pmtp__empty {
  padding: 24px 12px;
  text-align: center;
}

.pmtp__empty-hint {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.45);
}

.pmtp-tree {
  max-height: min(560px, calc(100vh - 220px));
  overflow: auto;
  padding: 4px 4px 8px;
}

:deep(.ant-tree-treenode) {
  min-width: 0;
}

:deep(.ant-tree-node-content-wrapper) {
  min-width: 0 !important;
  flex: 1 1 0 !important;
  border-radius: 6px;
}

:deep(.ant-tree-title) {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.pmtp-tree__title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding-right: 4px;
  box-sizing: border-box;
}

.pmtp-tree__row {
  display: flex;
  align-items: center;
  gap: 8px;
  gap: 8px;
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
}

.pmtp-tree__actions {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  flex-grow: 0;
  gap: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.pmtp-tree__action-btn {
  padding: 0 4px !important;
  height: 22px !important;
  line-height: 1 !important;
}

:deep(.ant-tree-treenode:hover) .pmtp-tree__actions,
:deep(.ant-tree-treenode-selected) .pmtp-tree__actions {
  opacity: 1;
}

.pmtp-tree__icon {
  flex-shrink: 0;
  color: #faad14;
  font-size: 14px;
}

.pmtp-tree__icon {
  flex-shrink: 0;
  color: #faad14;
  font-size: 14px;
}

.pmtp-tree__text {
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.ant-tree-node-selected .ant-tree-node-content-wrapper) {
  background: #e6f7ff !important;
}

.pmtp-create-form {
  margin-top: 8px;
}
</style>
