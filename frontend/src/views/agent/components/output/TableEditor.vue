<script setup lang="ts">
import { DeleteOutlined } from '@ant-design/icons-vue'
import { computed, nextTick, ref } from 'vue'
import type { TestCaseRow } from '../../types'

const props = defineProps<{
  columns: { title: string; dataIndex: string; key: string; width?: number; ellipsis?: boolean }[]
}>()

const rows = defineModel<TestCaseRow[]>('rows', { required: true })

const emit = defineEmits<{
  edited: []
}>()

const tableRows = computed(() => rows.value)

/** 当前处于编辑态的单元格：`${rowKey}::${dataIndex}` */
const editingCellKey = ref<string | null>(null)

const tableRootRef = ref<HTMLElement | null>(null)

function notifyEdited() {
  emit('edited')
}

function makeCellKey(rowKey: string, dataIndex: string) {
  return `${rowKey}::${dataIndex}`
}

function isEditing(rowKey: string, dataIndex: string) {
  return editingCellKey.value === makeCellKey(rowKey, dataIndex)
}

async function startEdit(rowKey: string, dataIndex: string) {
  editingCellKey.value = makeCellKey(rowKey, dataIndex)
  await nextTick()
  await nextTick()
  focusOpenedEditor()
}

/** 进入编辑后立刻聚焦 textarea / Select，避免仅靠 autofocus 在表格里不生效 */
function focusOpenedEditor() {
  const root = tableRootRef.value
  if (!root) return

  const textarea = root.querySelector('textarea.ant-input') as HTMLTextAreaElement | null
  if (textarea && root.contains(textarea)) {
    textarea.focus({ preventScroll: true })
    return
  }

  const selectSelector = root.querySelector(
    '.output-table__cell-select.output-table__cell-control--editing .ant-select-selector',
  ) as HTMLElement | null
  if (selectSelector && root.contains(selectSelector)) {
    selectSelector.focus({ preventScroll: true })
  }
}

function stopEdit() {
  editingCellKey.value = null
}

/** 焦点离开编辑区域（含点到表格外）则退出编辑态 */
function onEditorShellFocusOut(e: FocusEvent) {
  const shell = e.currentTarget as HTMLElement
  const rt = e.relatedTarget as Node | null
  if (rt && shell.contains(rt)) return
  stopEdit()
}

/** 优先级下拉关闭后再退出编辑态，避免抢焦点导致无法点开选项 */
function onPriorityDropdownVisibleChange(open: boolean, rowKey: string) {
  if (open) return
  if (!isEditing(rowKey, 'priority')) return
  window.setTimeout(() => {
    if (editingCellKey.value === makeCellKey(rowKey, 'priority')) {
      stopEdit()
    }
  }, 100)
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

function cellDisplayText(record: TestCaseRow, dataIndex: string): string {
  const raw = record[dataIndex as keyof TestCaseRow]
  if (raw === null || raw === undefined) return ''
  return String(raw)
}

function removeRow(rowKey: string) {
  rows.value = rows.value.filter((r) => r.key !== rowKey)
  if (editingCellKey.value?.startsWith(`${rowKey}::`)) {
    editingCellKey.value = null
  }
  notifyEdited()
}
</script>

<template>
  <div ref="tableRootRef" class="output-table">
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
          <div
            v-if="!isEditing(record.key, 'priority')"
            class="output-table__cell-display"
            tabindex="0"
            role="button"
            @dblclick="void startEdit(record.key, 'priority')"
            @keydown.enter.prevent="void startEdit(record.key, 'priority')"
          >
            {{ record.priority || '\u00a0' }}
          </div>
          <a-select
            v-else
            :value="record.priority"
            size="small"
            :bordered="true"
            class="output-table__cell-control output-table__cell-control--editing output-table__cell-select"
            :options="[
              { label: 'P0', value: 'P0' },
              { label: 'P1', value: 'P1' },
              { label: 'P2', value: 'P2' },
            ]"
            @change="(v: string) => updateCell(record.key, 'priority', v)"
            @dropdown-visible-change="(open: boolean) => onPriorityDropdownVisibleChange(open, record.key)"
          />
        </template>
        <template v-else-if="column.dataIndex === 'actions'">
          <div class="output-table__cell-actions">
            <a-button danger size="small" @click="removeRow(record.key)">
              <template #icon><DeleteOutlined /></template>
            </a-button>
          </div>
        </template>
        <template v-else>
          <div
            v-if="!isEditing(record.key, String(column.dataIndex))"
            class="output-table__cell-display output-table__cell-display--multiline"
            tabindex="0"
            role="button"
            @dblclick="void startEdit(record.key, String(column.dataIndex))"
            @keydown.enter.prevent="void startEdit(record.key, String(column.dataIndex))"
          >
            {{ cellDisplayText(record, String(column.dataIndex)) || '\u00a0' }}
          </div>
          <div
            v-else
            class="output-table__cell-edit-shell"
            tabindex="-1"
            @focusout="onEditorShellFocusOut"
          >
            <a-textarea
              :value="record[column.dataIndex]"
              :bordered="true"
              :rows="4"
              class="output-table__cell-control output-table__cell-control--editing"
              @change="
                (e: Event) =>
                  updateCell(record.key, String(column.dataIndex), (e.target as HTMLTextAreaElement).value)
              "
            />
          </div>
        </template>
      </template>
    </a-table>
  </div>
</template>

<style scoped lang="scss">
.output-table {
  --cell-editor-height: 92px;

  padding: 12px;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);

  :deep(.ant-table) {
    font-size: 12px;
  }

  /* 表头/单元格留一点内边距，不贴线框 */
  :deep(.ant-table .ant-table-cell) {
    padding: 6px 8px !important;
    vertical-align: top;
  }

  .output-table__cell-display {
    display: flex;
    align-items: flex-start;
    width: 100%;
    min-height: var(--cell-editor-height);
    padding: 0;
    box-sizing: border-box;
    line-height: 1.5;
    word-break: break-word;
    cursor: text;
    color: inherit;
    outline: none;
    border-radius: 2px;
    transition: background-color 0.15s ease;

    &:hover {
      background: rgba(0, 0, 0, 0.02);
    }

    &:focus-visible {
      box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.35);
    }

    &--multiline {
      white-space: pre-wrap;
    }
  }

  .output-table__cell-actions {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: var(--cell-editor-height);
    padding: 0;
    box-sizing: border-box;
  }

  .output-table__cell-edit-shell {
    width: 100%;
    min-height: var(--cell-editor-height);
    outline: none;
  }

  .output-table__cell-control--editing {
    width: 100%;
    margin: 0 !important;
    vertical-align: top;
  }

  :deep(.output-table__cell-control--editing textarea.ant-input) {
    width: 100% !important;
    height: var(--cell-editor-height) !important;
    min-height: var(--cell-editor-height) !important;
    max-height: var(--cell-editor-height) !important;
    padding: 4px 6px !important;
    box-sizing: border-box !important;
    resize: none !important;
    overflow-y: auto !important;
  }

  :deep(.output-table__cell-select.ant-select) {
    width: 100%;
    display: block;
  }

  :deep(.output-table__cell-select .ant-select-selector) {
    width: 100% !important;
    height: var(--cell-editor-height) !important;
    min-height: var(--cell-editor-height) !important;
    padding-inline: 6px !important;
    padding-block: 2px !important;
    border-radius: 6px !important;
  }

  :deep(.output-table__cell-select .ant-select-selection-item),
  :deep(.output-table__cell-select .ant-select-selection-placeholder) {
    line-height: calc(var(--cell-editor-height) - 8px) !important;
  }
}
</style>
