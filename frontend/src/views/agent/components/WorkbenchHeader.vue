<script setup lang="ts">
import {
  AppstoreOutlined,
  ColumnWidthOutlined,
  CommentOutlined,
} from '@ant-design/icons-vue'

type AgentLayoutMode = 'split' | 'output-only' | 'chat-only'

defineProps<{
  layoutMode: AgentLayoutMode
  title: string
  subtitle?: string
}>()

const emit = defineEmits<{
  'update:layout-mode': [mode: AgentLayoutMode]
}>()

const defaultSubtitle = '内容由智能 AI 生成，请仔细甄别'
</script>

<template>
  <div class="agent-page__workbench-head">
    <div class="agent-page__head-spacer" aria-hidden="true" />
    <div class="agent-page__head-center-block">
      <div class="agent-page__head-title">{{ title }}</div>
      <div class="agent-page__head-subtitle">{{ subtitle ?? defaultSubtitle }}</div>
    </div>
    <div class="agent-page__head-right">
      <a-radio-group
        size="small"
        :value="layoutMode"
        button-style="solid"
        @update:value="emit('update:layout-mode', $event)"
      >
        <a-radio-button value="split">
          <a-tooltip title="双栏">
            <ColumnWidthOutlined />
          </a-tooltip>
        </a-radio-button>
        <a-radio-button value="output-only">
          <a-tooltip title="仅输出区">
            <AppstoreOutlined />
          </a-tooltip>
        </a-radio-button>
        <a-radio-button value="chat-only">
          <a-tooltip title="仅对话区">
            <CommentOutlined />
          </a-tooltip>
        </a-radio-button>
      </a-radio-group>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-page__workbench-head {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) auto minmax(120px, 1fr);
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.agent-page__head-spacer {
  min-width: 0;
}

.agent-page__head-center-block {
  text-align: center;
  min-width: 0;
  grid-column: 2;
}

.agent-page__head-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  line-height: 1.35;
}

.agent-page__head-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
}

.agent-page__head-right {
  grid-column: 3;
  justify-self: end;
  flex-shrink: 0;
}

@media (max-width: 576px) {
  .agent-page__workbench-head {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }

  .agent-page__head-center-block {
    grid-column: 1;
    grid-row: 1;
  }

  .agent-page__head-right {
    grid-column: 1;
    grid-row: 2;
    justify-self: center;
  }

  .agent-page__head-spacer {
    display: none;
  }
}
</style>
