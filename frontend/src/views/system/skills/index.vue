<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { createSkill, deleteSkill, listAdminSkills, updateSkill } from '@/api/adminSkills'
import { listSkills } from '@/api/skills'
import type { SkillAdmin, SkillMetaOut } from '@/schemas/skill'

const loading = ref(false)
const tableData = ref<SkillAdmin[]>([])
const keyword = ref('')

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const registeredSkills = ref<SkillMetaOut[]>([])

const modalOpen = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)

const form = reactive({
  skill_id: '',
  name: '',
  description: '',
  capability_tags: [] as string[],
  tagInput: '',
  icon_key: '',
  is_published: true,
  sort_order: 0
})

const skillIdOptions = computed(() => {
  const base = registeredSkills.value.map((s) => ({
    label: `${s.skill_id} — ${s.name}`,
    value: s.skill_id
  }))
  if (form.skill_id && !base.some((o) => o.value === form.skill_id)) {
    return [{ label: form.skill_id, value: form.skill_id }, ...base]
  }
  return base
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 72 },
  { title: 'skill_id', dataIndex: 'skill_id', key: 'skill_id', ellipsis: true },
  { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '上架', key: 'pub', width: 72 },
  { title: '运行时', key: 'runtime', width: 88 },
  { title: '使用次数', dataIndex: 'use_count', key: 'use_count', width: 96 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 72 },
  { title: '操作', key: 'actions', width: 160, fixed: 'right' as const }
]

async function loadTable() {
  loading.value = true
  try {
    const res = await listAdminSkills({
      page: pagination.current,
      size: pagination.pageSize,
      q: keyword.value.trim() || undefined
    })
    tableData.value = res.data?.items ?? []
    pagination.total = res.data?.total ?? 0
  } catch {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadRegistered() {
  try {
    const res = await listSkills()
    registeredSkills.value = res.data ?? []
  } catch {
    registeredSkills.value = []
  }
}

onMounted(() => {
  void loadRegistered()
  void loadTable()
})

function openCreate() {
  editingId.value = null
  form.skill_id = registeredSkills.value[0]?.skill_id ?? ''
  form.name = ''
  form.description = ''
  form.capability_tags = []
  form.tagInput = ''
  form.icon_key = ''
  form.is_published = true
  form.sort_order = 0
  modalOpen.value = true
}

function openEdit(row: SkillAdmin) {
  editingId.value = row.id
  form.skill_id = row.skill_id
  form.name = row.name
  form.description = row.description
  form.capability_tags = [...(row.capability_tags ?? [])]
  form.tagInput = ''
  form.icon_key = row.icon_key ?? ''
  form.is_published = row.is_published
  form.sort_order = row.sort_order
  modalOpen.value = true
}

function addTag() {
  const t = form.tagInput.trim()
  if (!t) return
  if (!form.capability_tags.includes(t)) form.capability_tags.push(t)
  form.tagInput = ''
}

function removeTag(tag: string) {
  form.capability_tags = form.capability_tags.filter((x) => x !== tag)
}

async function submit() {
  if (!form.skill_id.trim() || !form.name.trim()) {
    message.warning('请填写 skill_id 与名称')
    return
  }
  saving.value = true
  try {
    const body = {
      skill_id: form.skill_id.trim(),
      name: form.name.trim(),
      description: form.description,
      capability_tags: form.capability_tags,
      icon_key: form.icon_key.trim() || null,
      is_published: form.is_published,
      sort_order: form.sort_order
    }
    if (editingId.value == null) {
      await createSkill(body)
      message.success('已创建')
    } else {
      await updateSkill(editingId.value, body)
      message.success('已保存')
    }
    modalOpen.value = false
    await loadTable()
  } catch (e: unknown) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

function confirmDelete(row: SkillAdmin) {
  Modal.confirm({
    title: '删除技能目录项？',
    content: `将软删除「${row.name}」（${row.skill_id}）。`,
    okType: 'danger',
    onOk: async () => {
      await deleteSkill(row.id)
      message.success('已删除')
      await loadTable()
    }
  })
}

function handleSearch() {
  pagination.current = 1
  void loadTable()
}

function handlePaginationChange(page: number, pageSize: number) {
  pagination.pageSize = pageSize
  pagination.current = page
  void loadTable()
}
</script>

<template>
  <div class="skills">
    <a-card class="main-card" :bordered="false">
      <div class="block search-row">
        <a-space wrap :size="12">
          <a-input
            v-model:value="keyword"
            allow-clear
            placeholder="搜索名称 / skill_id / 描述"
            style="width: 260px"
            @pressEnter="handleSearch"
          />
          <a-button type="primary" @click="handleSearch"><SearchOutlined />搜索</a-button>
        </a-space>
      </div>

      <div class="block toolbar-row">
        <a-button type="primary" @click="openCreate"><PlusOutlined />新建技能</a-button>
      </div>

      <div class="block table-block">
        <a-table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          :pagination="false"
          row-key="id"
          :scroll="{ x: 960 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'pub'">
              <a-tag :color="record.is_published ? 'green' : 'default'">
                {{ record.is_published ? '上架' : '下架' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'runtime'">
              <a-tag :color="record.runtime_available ? 'blue' : 'orange'">
                {{ record.runtime_available ? '已注册' : '未注册' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
                <a-button type="link" danger size="small" @click="confirmDelete(record)">删除</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>

      <div class="block pagination-row">
        <a-pagination
          :current="pagination.current"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(t: number) => `共 ${t} 条`"
          :page-size-options="['10', '20', '50']"
          @change="handlePaginationChange"
        />
      </div>
    </a-card>

    <a-modal
      v-model:open="modalOpen"
      :title="editingId == null ? '新建技能目录' : '编辑技能目录'"
      width="720px"
      :confirm-loading="saving"
      destroy-on-close
      @ok="submit"
    >
      <a-form layout="vertical">
        <a-form-item label="skill_id（与 backend/skills 目录一致）" required>
          <a-select
            v-if="registeredSkills.length"
            v-model:value="form.skill_id"
            show-search
            :options="skillIdOptions"
            placeholder="选择已注册技能"
            :disabled="editingId != null"
          />
          <a-input v-else v-model:value="form.skill_id" placeholder="暂无注册技能，可手动填写 skill_id" />
        </a-form-item>
        <a-form-item label="展示名称" required>
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item label="列表短描述">
          <a-textarea v-model:value="form.description" :rows="3" />
        </a-form-item>
        <a-form-item label="核心能力标签">
          <div class="tag-row">
            <a-input
              v-model:value="form.tagInput"
              placeholder="输入后回车添加"
              style="max-width: 280px"
              @pressEnter.prevent="addTag"
            />
            <a-button size="small" @click="addTag">添加</a-button>
          </div>
          <div class="tags">
            <a-tag v-for="t in form.capability_tags" :key="t" closable @close="removeTag(t)">{{ t }}</a-tag>
          </div>
        </a-form-item>
        <a-form-item label="图标 key">
          <a-input v-model:value="form.icon_key" placeholder="可选" />
        </a-form-item>
        <a-form-item label="上架（开启后在技能广场展示）">
          <a-switch v-model:checked="form.is_published" />
        </a-form-item>
        <a-form-item label="排序（越小越靠前）">
          <a-input-number v-model:value="form.sort_order" :min="0" style="width: 120px" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped lang="scss">
.skills {
  padding: 0;
}
.main-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.block + .block {
  margin-top: 16px;
}
.search-row {
  padding-bottom: 4px;
}
.toolbar-row {
  padding-bottom: 0;
}
.pagination-row {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
