<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  AppstoreOutlined,
  ColumnWidthOutlined,
  CommentOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  HistoryOutlined,
  PlusOutlined,
  RobotOutlined
} from '@ant-design/icons-vue'
import SessionHistoryDrawer from './chat-panel/SessionHistoryDrawer.vue'

type AgentLayoutMode = 'split' | 'output-only' | 'chat-only'

const props = defineProps<{
  sessionId: string | null
  layoutMode: AgentLayoutMode
  immersiveMode: boolean
}>()

const emit = defineEmits<{
  'update:layout-mode': [mode: AgentLayoutMode]
  'toggle-immersive': []
  'new-session': []
  'select-history-session': [payload: { sessionId: string; skillId: string }]
}>()

const historyOpen = ref(false)

const sessionText = computed(() => {
  if (!props.sessionId) return '未建立'
  return `${props.sessionId.slice(0, 8)}…`
})
</script>

<template>
  <div class="agent-page__workbench-head">
    <div class="agent-page__head-left">
      <span class="agent-page__head-title">
        <RobotOutlined />
        <span>测试智能体</span>
      </span>
      <span class="agent-page__head-session" :title="sessionId || undefined"> 会话：{{ sessionText }} </span>
    </div>
    <div class="agent-page__head-center">
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
    <div class="agent-page__head-actions">
      <a-tooltip :title="immersiveMode ? '退出沉浸模式' : '沉浸模式'">
        <a-button
          type="text"
          size="small"
          :class="{ 'agent-page__max-btn--active': immersiveMode }"
          @click="emit('toggle-immersive')"
        >
          <template #icon>
            <FullscreenOutlined v-if="!immersiveMode" />
            <FullscreenExitOutlined v-else />
          </template>
        </a-button>
      </a-tooltip>
      <a-button type="text" size="small" title="新会话" @click="emit('new-session')">
        <template #icon><PlusOutlined /></template>
        新会话
      </a-button>
      <SessionHistoryDrawer v-model:open="historyOpen" @select="emit('select-history-session', $event)">
        <a-button type="text" size="small" title="历史会话">
          <template #icon><HistoryOutlined /></template>
          历史
        </a-button>
      </SessionHistoryDrawer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-page__workbench-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.agent-page__head-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.agent-page__head-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.agent-page__head-session {
  color: #8c8c8c;
  font-size: 12px;
  font-family: Consolas, Monaco, monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.agent-page__head-center {
  flex-shrink: 0;
}

.agent-page__head-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.agent-page__max-btn--active {
  color: #1677ff;
  background: #e6f4ff;
}
</style>

