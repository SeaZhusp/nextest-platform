<script setup lang="ts">
import { DeleteOutlined } from '@ant-design/icons-vue'
import { computed } from 'vue'
import type { TestCaseRow } from '../../types'

const props = defineProps<{
  columns: { title: string; dataIndex: string; key: string; width?: number; ellipsis?: boolean }[]
}>()

const rows = defineModel<TestCaseRow[]>('rows', { required: true })

const emit = defineEmits<{
  edited: []
}>()

const tableRows = computed(() => rows.value)

function notifyEdited() {
  emit('edited')
}

function updateCell(rowKey: string, field: string, value: string) {
  const row = rows.value.find((r) => r.key === rowKey)
  if (!row) return
  if (
    field === 'case_no' ||
    field === 'module' ||
    field === 'title' ||
    field === 'preconditions' ||
    field === 'steps' ||
    field === 'expected' ||
    field === 'priority'
  ) {
    row[field] = value
    notifyEdited()
  }
}

function isMultilineField(field: string): boolean {
  return field === 'preconditions' || field === 'steps' || field === 'expected'
}

function removeRow(rowKey: string) {
  rows.value = rows.value.filter((r) => r.key !== rowKey)
  notifyEdited()
}
</script>

<template>
  <div class="output-table">
    <a-table
      :columns="props.columns"
      :data-source="tableRows"
      :pagination="false"
      :scroll="{ x: 1100 }"
      size="small"
      bordered
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'priority'">
          <a-select
            :value="record.priority"
            size="small"
            style="width: 60px"
            :options="[
              { label: 'P0', value: 'P0' },
              { label: 'P1', value: 'P1' },
              { label: 'P2', value: 'P2' }
            ]"
            @change="(v: string) => updateCell(record.key, 'priority', v)"
          />
        </template>
        <template v-else-if="column.dataIndex === 'actions'">
          <a-button danger size="small" @click="removeRow(record.key)">
            <template #icon><DeleteOutlined /></template>
          </a-button>
        </template>
        <template v-else>
          <a-textarea
            v-if="isMultilineField(String(column.dataIndex))"
            :value="record[column.dataIndex]"
            :auto-size="{ minRows: 1, maxRows: 6 }"
            @change="(e: Event) => updateCell(record.key, String(column.dataIndex), (e.target as HTMLTextAreaElement).value)"
          />
          <a-input
            v-else
            :value="record[column.dataIndex]"
            size="small"
            @change="(e: Event) => updateCell(record.key, String(column.dataIndex), (e.target as HTMLInputElement).value)"
          />
        </template>
      </template>
    </a-table>
  </div>
</template>

<style scoped lang="scss">
.output-table {
  padding: 12px;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);

  :deep(.ant-table) {
    font-size: 12px;
  }
}
</style>
