<script setup lang="ts">
import { watch } from 'vue'
import {
  HistoryOutlined,
  SaveOutlined,
  UnorderedListOutlined
} from '@ant-design/icons-vue'
import type { AgentOutputTabKey, DocumentModel } from '../types'
import TableEditor from './output/TableEditor.vue'

const props = defineProps<{
  sessionId: string | null
  canRestoreRaw: boolean
  tableColumns: { title: string; dataIndex: string; key: string; width?: number; ellipsis?: boolean }[]
}>()

const documentModel = defineModel<DocumentModel>('document', { required: true })
const outputTab = defineModel<AgentOutputTabKey>('outputTab', { default: 'table' })

const emit = defineEmits<{
  save: []
  restoreRaw: []
}>()

watch(
  () => outputTab.value,
  (tab) => {
    if (tab !== 'table') {
      outputTab.value = 'table'
    }
  },
  { immediate: true }
)

function markEdited(by: AgentOutputTabKey) {
  documentModel.value.sync.revision += 1
  documentModel.value.sync.lastEditedBy = by
  documentModel.value.sync.lastEditedAt = Date.now()
}

function onSave() {
  emit('save')
}

function onRestoreRaw() {
  emit('restoreRaw')
}
</script>

<template>
  <section class="agent-output">
    <div class="agent-output__toolbar">
      <div class="agent-output__actions">
        <a-button size="small" :disabled="!props.canRestoreRaw" @click="onRestoreRaw">
          <template #icon>
            <HistoryOutlined />
          </template>
          恢复原始版
        </a-button>
        <a-button type="primary" size="small" @click="onSave">
          <template #icon>
            <SaveOutlined />
          </template>
          保存
        </a-button>
      </div>
    </div>

    <a-tabs v-model:activeKey="outputTab" class="agent-output__tabs" type="card">
      <a-tab-pane key="table">
        <template #tab>
          <span><UnorderedListOutlined /> 表格</span>
        </template>
        <div class="agent-output__pane agent-output__pane--table">
          <TableEditor
            v-model:rows="documentModel.tableRows"
            :columns="tableColumns"
            @edited="markEdited('table')"
          />
        </div>
      </a-tab-pane>
    </a-tabs>
  </section>
</template>

<style lang="scss" scoped>
.agent-output {
  flex: 1;
  min-width: 0;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  color: #262626;
}

.agent-output__toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.agent-output__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-output__tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;

  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 0 8px;
    background: #fff;
    border-bottom: 1px solid #f0f0f0;

    &::before {
      border-bottom: 1px solid #f0f0f0;
    }
  }

  :deep(.ant-tabs-tab) {
    color: #595959 !important;
    border: 1px solid transparent !important;
    background: #fff !important;

    &.ant-tabs-tab-active .ant-tabs-tab-btn {
      color: #1677ff !important;
    }
  }

  :deep(.ant-tabs-content-holder) {
    flex: 1;
    min-height: 0;
  }

  :deep(.ant-tabs-content) {
    height: 100%;
  }

  :deep(.ant-tabs-tabpane) {
    height: 100%;
  }
}

.agent-output__pane {
  height: calc(100vh - 280px);
  min-height: 360px;
  overflow: auto;
}

.agent-output__pane--table {
  padding: 0;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);
}
</style>
