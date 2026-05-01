<script setup lang="ts">
import { ref } from 'vue'
import { PlusOutlined, HistoryOutlined, RobotOutlined } from '@ant-design/icons-vue'
import SessionHistoryDrawer from './SessionHistoryDrawer.vue'

const emit = defineEmits<{
  'new-session': []
  'select-history-session': [payload: { sessionId: string; skillId: string }]
}>()

const historyOpen = ref(false)
</script>

<template>
  <header class="agent-chat__header">
    <div class="agent-chat__title">
      <RobotOutlined class="agent-chat__title-icon" />
      <span>测试智能体</span>
    </div>
    <div class="agent-chat__header-actions">
      <a-button type="text" size="small" title="新会话" @click="emit('new-session')">
        <PlusOutlined />
      </a-button>
      <SessionHistoryDrawer v-model:open="historyOpen" @select="emit('select-history-session', $event)">
        <a-button type="text" size="small" title="历史">
          <HistoryOutlined />
        </a-button>
      </SessionHistoryDrawer>
    </div>
  </header>
</template>

<style scoped lang="scss">
.agent-chat__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.agent-chat__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #262626;
}

.agent-chat__title-icon {
  font-size: 20px;
  color: #1890ff;
}

.agent-chat__header-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}
</style>
