<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { SaveOutlined, UnorderedListOutlined } from '@ant-design/icons-vue'
import type { AgentOutputTabKey } from '../types'

const props = defineProps<{
  sessionId: string | null
  tableColumns: { title: string; dataIndex: string; key: string; width?: number; ellipsis?: boolean }[]
  rows: Record<string, unknown>[]
  markdownReport: string
}>()

const editorJson = defineModel<string>('editorJson', { required: true })
const outputTab = defineModel<AgentOutputTabKey>('outputTab', { default: 'table' })

const emit = defineEmits<{
  save: []
}>()

const previewHtml = computed(() => {
  const raw = marked.parse(props.markdownReport, { async: false })
  const html = typeof raw === 'string' ? raw : ''
  return DOMPurify.sanitize(html)
})

function onSave() {
  emit('save')
}
</script>

<template>
  <section class="agent-output">
    <div class="agent-output__toolbar">
      <div class="agent-output__title-block">
        <span class="agent-output__title">输出区</span>
        <span class="agent-output__session" :title="sessionId || undefined">
          会话：{{
            sessionId ? sessionId.slice(0, 8) + '…' : '未建立（发送后由后端分配）'
          }}
        </span>
      </div>
      <div class="agent-output__actions">
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
          <a-table
            :columns="tableColumns"
            :data-source="rows"
            :pagination="false"
            :scroll="{ x: 1100, y: 'calc(100vh - 320px)' }"
            size="small"
            bordered
          />
        </div>
      </a-tab-pane>

      <a-tab-pane key="editor">
        <template #tab>
          <span>编辑器</span>
        </template>
        <div class="agent-output__pane agent-output__pane--editor">
          <textarea
            v-model="editorJson"
            class="agent-editor"
            spellcheck="false"
            aria-label="JSON 编辑器"
          />
        </div>
      </a-tab-pane>

      <a-tab-pane key="preview">
        <template #tab>
          <span>预览</span>
        </template>
        <div class="agent-output__pane agent-output__pane--preview">
          <article class="markdown-body" v-html="previewHtml" />
        </div>
      </a-tab-pane>
    </a-tabs>
  </section>
</template>

<style lang="scss" scoped>
.agent-output {
  flex: 1.25;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
  border-right: 1px solid #333;
}

.agent-output__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #252526;
  border-bottom: 1px solid #333;
}

.agent-output__title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.agent-output__title {
  font-weight: 600;
  font-size: 14px;
  color: #ccc;
}

.agent-output__session {
  font-size: 11px;
  color: #888;
  font-family: Consolas, Monaco, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 240px;
}

.agent-output__tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;

  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 0 8px;
    background: #252526;
    border-bottom: 1px solid #333;

    &::before {
      border: none;
    }
  }

  :deep(.ant-tabs-tab) {
    color: #aaa !important;
    border: 1px solid transparent !important;
    background: transparent !important;

    &.ant-tabs-tab-active .ant-tabs-tab-btn {
      color: #fff !important;
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
  padding: 12px;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);

  :deep(.ant-table) {
    font-size: 12px;
  }
}

.agent-output__pane--editor {
  padding: 0;
  background: #1e1e1e;
}

.agent-editor {
  width: 100%;
  height: 100%;
  min-height: 360px;
  padding: 12px 16px;
  margin: 0;
  border: none;
  resize: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  background: #1e1e1e;
  outline: none;
}

.agent-output__pane--preview {
  padding: 16px 20px;
  background: #fff;
  color: #24292f;
}

.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  max-width: 720px;

  :deep(h1) {
    font-size: 1.35rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.35em;
    margin-top: 0;
  }

  :deep(h2) {
    font-size: 1.15rem;
    margin-top: 1em;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 13px;
  }

  :deep(th),
  :deep(td) {
    border: 1px solid #d0d7de;
    padding: 6px 10px;
  }

  :deep(th) {
    background: #f6f8fa;
  }

  :deep(pre) {
    background: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow: auto;
    font-size: 12px;
  }

  :deep(code) {
    font-family: Consolas, Monaco, monospace;
    font-size: 0.9em;
  }
}
</style>
