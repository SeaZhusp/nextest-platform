<script setup lang="ts">
import { PlusOutlined, HistoryOutlined, RobotOutlined } from '@ant-design/icons-vue'

const emit = defineEmits<{
  'new-session': []
  history: []
}>()
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
      <a-button type="text" size="small" title="历史" @click="emit('history')">
        <HistoryOutlined />
      </a-button>
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
}
</style>
