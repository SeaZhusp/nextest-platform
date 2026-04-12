<script setup lang="ts">
import type { AgentChatMessage } from '../../types'

defineProps<{
  messages: AgentChatMessage[]
}>()
</script>

<template>
  <div class="agent-chat__messages">
    <div
      v-for="m in messages"
      :key="m.id"
      class="agent-msg"
      :class="m.role === 'user' ? 'agent-msg--user' : 'agent-msg--assistant'"
    >
      <a-avatar
        class="agent-msg__avatar"
        :style="{
          backgroundColor: m.role === 'user' ? '#1890ff' : '#52c41a'
        }"
      >
        {{ m.role === 'user' ? '我' : 'AI' }}
      </a-avatar>
      <div class="agent-msg__bubble">{{ m.content }}</div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-chat__messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
}

.agent-msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.agent-msg--user {
  flex-direction: row-reverse;

  .agent-msg__bubble {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
  }
}

.agent-msg__avatar {
  flex-shrink: 0;
}

.agent-msg__bubble {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #f0f0f0;
  font-size: 13px;
  line-height: 1.55;
  color: #434343;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
