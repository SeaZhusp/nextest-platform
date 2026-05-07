<script setup lang="ts">
/**
 * Agent 输出区用例表：底层为通用 EditableTable，保持原有 props / v-model / 事件。
 */
import { computed } from 'vue'
import EditableTable from '@/components/EditableTable/index.vue'
import type { EditableTableRow } from '@/components/EditableTable/types'
import type { TestCaseRow } from '../../types'

const props = defineProps<{
  columns: { title: string; dataIndex: string; key: string; width?: number; ellipsis?: boolean }[]
}>()

const rows = defineModel<TestCaseRow[]>('rows', { required: true })

const emit = defineEmits<{
  edited: []
}>()

const editableRows = computed<EditableTableRow[]>({
  get: () => rows.value as unknown as EditableTableRow[],
  set: (v) => {
    rows.value = v as unknown as TestCaseRow[]
  },
})
</script>

<template>
  <EditableTable
    v-model:rows="editableRows"
    :columns="props.columns"
    @edited="emit('edited')"
  />
</template>
