<script setup lang="ts">
/**
 * 通用可编辑表格：双击/Enter 进入 textarea 编辑，失焦退出；可选行多选；操作列/模块列由插槽扩展。
 */
import { DeleteOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { computed, nextTick, ref, useSlots } from 'vue'
import type { EditableTableColumn, EditableTableRow } from './types'

const props = withDefaults(
  defineProps<{
    columns: EditableTableColumn[]
    /** 为表格绑定 Ant Design `row-selection`（选中态由父组件维护） */
    rowSelection?: TableProps['rowSelection'] | null
    /** 横向滚动宽度等，与 a-table scroll 一致 */
    scroll?: TableProps['scroll']
    /** 除内置可编辑列外，允许写入的 dataIndex（如 status、module_id） */
    extraEditableFields?: string[]
    /** 使用内置「优先级」下拉列的 dataIndex，默认 `priority`；设为 `''` 则禁用该内置列 */
    priorityColumnKey?: string
    /** 内置优先级下拉的选项 */
    priorityOptions?: { label: string; value: string }[]
    /** 识别为「操作列」的 dataIndex，默认 `actions` */
    actionsColumnKey?: string
  }>(),
  {
    rowSelection: undefined,
    scroll: () => ({ x: 1100 }),
    extraEditableFields: () => [],
    priorityColumnKey: 'priority',
    priorityOptions: () => [
      { label: 'P0', value: 'P0' },
      { label: 'P1', value: 'P1' },
      { label: 'P2', value: 'P2' },
    ],
    actionsColumnKey: 'actions',
  },
)

const rows = defineModel<EditableTableRow[]>('rows', { required: true })

const emit = defineEmits<{
  edited: []
}>()

const slots = useSlots()
const hasModuleCellSlot = computed(() => typeof slots['module-cell'] === 'function')

const tableRows = computed(() => rows.value)

const editingCellKey = ref<string | null>(null)
const tableRootRef = ref<HTMLElement | null>(null)

const builtInEditable = new Set([
  'case_no',
  'module',
  'title',
  'preconditions',
  'steps',
  'expected',
  'priority',
])

function isFieldEditable(field: string): boolean {
  if (builtInEditable.has(field)) return true
  return props.extraEditableFields.includes(field)
}

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

function focusOpenedEditor() {
  const root = tableRootRef.value
  if (!root) return

  const textarea = root.querySelector('textarea.ant-input') as HTMLTextAreaElement | null
  if (textarea && root.contains(textarea)) {
    textarea.focus({ preventScroll: true })
    return
  }

  const selectSelector = root.querySelector(
    '.editable-table__cell-select.editable-table__cell-control--editing .ant-select-selector',
  ) as HTMLElement | null
  if (selectSelector && root.contains(selectSelector)) {
    selectSelector.focus({ preventScroll: true })
  }
}

function stopEdit() {
  editingCellKey.value = null
}

function onEditorShellFocusOut(e: FocusEvent) {
  const shell = e.currentTarget as HTMLElement
  const rt = e.relatedTarget as Node | null
  if (rt && shell.contains(rt)) return
  stopEdit()
}

function onPriorityDropdownVisibleChange(open: boolean, rowKey: string) {
  if (open) return
  const pk = props.priorityColumnKey
  if (!pk || !isEditing(rowKey, pk)) return
  window.setTimeout(() => {
    if (editingCellKey.value === makeCellKey(rowKey, pk)) {
      stopEdit()
    }
  }, 100)
}

function updateCell(rowKey: string, field: string, value: string) {
  const row = rows.value.find((r) => r.key === rowKey)
  if (!row) return
  if (!isFieldEditable(field)) return
  ;(row as Record<string, unknown>)[field] = value
  notifyEdited()
}

function cellDisplayText(record: EditableTableRow, dataIndex: string): string {
  const raw = record[dataIndex]
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
  <div ref="tableRootRef" class="editable-table">
    <div v-if="$slots.toolbar" class="editable-table__toolbar">
      <slot name="toolbar" />
    </div>

    <a-table
      :columns="columns"
      :data-source="tableRows"
      :pagination="false"
      :scroll="scroll"
      :row-selection="rowSelection ?? undefined"
      size="small"
      bordered
    >
      <template #bodyCell="{ column, record }">
        <template
          v-if="priorityColumnKey && String(column.dataIndex) === priorityColumnKey"
        >
          <div
            v-if="!isEditing(record.key, priorityColumnKey)"
            class="editable-table__cell-display"
            tabindex="0"
            role="button"
            @dblclick="void startEdit(record.key, priorityColumnKey)"
            @keydown.enter.prevent="void startEdit(record.key, priorityColumnKey)"
          >
            {{ cellDisplayText(record, priorityColumnKey) || '\u00a0' }}
          </div>
          <a-select
            v-else
            :value="record[priorityColumnKey]"
            size="small"
            :bordered="true"
            class="editable-table__cell-control editable-table__cell-control--editing editable-table__cell-select"
            :options="priorityOptions"
            @change="(v: string) => updateCell(record.key, priorityColumnKey, v)"
            @dropdown-visible-change="
              (open: boolean) => onPriorityDropdownVisibleChange(open, record.key)
            "
          />
        </template>

        <template v-else-if="String(column.dataIndex) === actionsColumnKey">
          <div class="editable-table__cell-actions">
            <slot name="actions" :record="record" :remove-row="removeRow">
              <a-button danger size="small" @click="removeRow(record.key)">
                <template #icon><DeleteOutlined /></template>
              </a-button>
            </slot>
          </div>
        </template>

        <template
          v-else-if="String(column.dataIndex) === 'module' && hasModuleCellSlot"
        >
          <slot name="module-cell" :record="record" :column="column" />
        </template>

        <template v-else>
          <div
            v-if="!isEditing(record.key, String(column.dataIndex))"
            class="editable-table__cell-display editable-table__cell-display--multiline"
            tabindex="0"
            role="button"
            @dblclick="void startEdit(record.key, String(column.dataIndex))"
            @keydown.enter.prevent="void startEdit(record.key, String(column.dataIndex))"
          >
            {{ cellDisplayText(record, String(column.dataIndex)) || '\u00a0' }}
          </div>
          <div
            v-else
            class="editable-table__cell-edit-shell"
            tabindex="-1"
            @focusout="onEditorShellFocusOut"
          >
            <a-textarea
              :value="String(record[column.dataIndex] ?? '')"
              :bordered="true"
              :rows="4"
              class="editable-table__cell-control editable-table__cell-control--editing"
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
.editable-table {
  --cell-editor-height: 92px;

  padding: 12px;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);

  :deep(.ant-table) {
    font-size: 12px;
  }

  :deep(.ant-table .ant-table-cell) {
    padding: 6px 8px !important;
    vertical-align: top;
  }

  &__toolbar {
    margin-bottom: 10px;
  }

  &__cell-display {
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

  &__cell-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: var(--cell-editor-height);
    padding: 0;
    box-sizing: border-box;
  }

  &__cell-edit-shell {
    width: 100%;
    min-height: var(--cell-editor-height);
    outline: none;
  }

  &__cell-control--editing {
    width: 100%;
    margin: 0 !important;
    vertical-align: top;
  }

  :deep(.editable-table__cell-control--editing textarea.ant-input) {
    width: 100% !important;
    height: var(--cell-editor-height) !important;
    min-height: var(--cell-editor-height) !important;
    max-height: var(--cell-editor-height) !important;
    padding: 4px 6px !important;
    box-sizing: border-box !important;
    resize: none !important;
    overflow-y: auto !important;
  }

  :deep(.editable-table__cell-select.ant-select) {
    width: 100%;
    display: block;
  }

  :deep(.editable-table__cell-select .ant-select-selector) {
    width: 100% !important;
    height: var(--cell-editor-height) !important;
    min-height: var(--cell-editor-height) !important;
    padding-inline: 6px !important;
    padding-block: 2px !important;
    border-radius: 6px !important;
  }

  :deep(.editable-table__cell-select .ant-select-selection-item),
  :deep(.editable-table__cell-select .ant-select-selection-placeholder) {
    line-height: calc(var(--cell-editor-height) - 8px) !important;
  }
}
</style>
