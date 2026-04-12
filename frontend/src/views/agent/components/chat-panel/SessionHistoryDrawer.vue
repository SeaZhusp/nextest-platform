<script setup lang="ts">
import { ref, watch } from 'vue'
import { EditOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { TableColumnType } from 'ant-design-vue'
import { getAgentSessions, patchAgentSessionTitle } from '@/api/agent'
import type { AgentSessionSummaryOut } from '@/schemas/agent'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  'update:open': [v: boolean]
  select: [payload: { sessionId: string; skillId: string }]
}>()

const loading = ref(false)
const items = ref<AgentSessionSummaryOut[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const renameVisible = ref(false)
const renameSubmitting = ref(false)
const renameInput = ref('')
const renameTarget = ref<AgentSessionSummaryOut | null>(null)

const columns: TableColumnType<AgentSessionSummaryOut>[] = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 172 },
  { title: '', key: 'actions', width: 56, align: 'center' }
]

async function load() {
  if (!props.open) return
  loading.value = true
  try {
    const res = await getAgentSessions({ page: page.value, size: pageSize.value })
    items.value = res.data?.items ?? []
    total.value = res.data?.total ?? 0
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  () => props.open,
  (v) => {
    if (v) {
      page.value = 1
      void load()
    }
  }
)

function close() {
  emit('update:open', false)
}

function onRowClick(record: AgentSessionSummaryOut) {
  emit('select', { sessionId: record.session_id, skillId: record.skill_id })
  close()
}

function onTableChange(pagination: { current?: number; pageSize?: number }) {
  if (pagination.current != null) page.value = pagination.current
  if (pagination.pageSize != null) pageSize.value = pagination.pageSize
  void load()
}

function openRename(record: AgentSessionSummaryOut) {
  renameTarget.value = record
  renameInput.value = record.title || ''
  renameVisible.value = true
}

async function handleRenameOk() {
  const t = renameInput.value.trim()
  if (!t) {
    message.warning('请输入标题')
    return
  }
  const row = renameTarget.value
  if (!row) return
  renameSubmitting.value = true
  try {
    await patchAgentSessionTitle(row.session_id, { title: t })
    message.success('已保存')
    renameVisible.value = false
    renameTarget.value = null
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    renameSubmitting.value = false
  }
}
</script>

<template>
  <a-drawer :open="open" title="历史会话" placement="right" :width="440" @close="close">
    <a-table
      size="small"
      :columns="columns"
      :data-source="items"
      :loading="loading"
      row-key="session_id"
      :pagination="{
        current: page,
        pageSize,
        total,
        showSizeChanger: true,
        pageSizeOptions: ['10', '20', '50'],
        showTotal: (t: number) => `共 ${t} 条`
      }"
      :custom-row="
        (record: AgentSessionSummaryOut) => ({
          onClick: () => onRowClick(record),
          style: { cursor: 'pointer' }
        })
      "
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'title'">
          {{ (record.title || '').trim() || '（无标题）' }}
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button type="link" size="small" @click.stop="openRename(record as AgentSessionSummaryOut)">
            <template #icon>
              <EditOutlined />
            </template>
          </a-button>
        </template>
      </template>
      <template #emptyText>
        <span class="session-history__empty">暂无会话记录，发送一条消息后会出现在这里</span>
      </template>
    </a-table>

    <a-modal
      v-model:open="renameVisible"
      title="重命名会话"
      :confirm-loading="renameSubmitting"
      ok-text="保存"
      destroy-on-close
      @ok="handleRenameOk"
    >
      <a-input v-model:value="renameInput" maxlength="200" show-count placeholder="会话标题" />
    </a-modal>
  </a-drawer>
</template>

<style scoped lang="scss">
.session-history__empty {
  color: #8c8c8c;
  font-size: 13px;
}
</style>
