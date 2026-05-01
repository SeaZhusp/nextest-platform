<script setup lang="ts">
import { CheckCircleTwoTone, CloseCircleTwoTone, LoadingOutlined } from '@ant-design/icons-vue'
import { nextTick, ref, watch } from 'vue'
import type { AgentChatMessage } from '../../types'

const props = defineProps<{
  messages: AgentChatMessage[]
}>()

const emit = defineEmits<{
  'show-output': []
}>()

const messageListRef = ref<HTMLElement | null>(null)
const streamBoxRefs = ref<Record<string, HTMLElement>>({})

function scrollToBottom() {
  const el = messageListRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

function setStreamBoxRef(messageId: string, el: unknown) {
  if (el instanceof HTMLElement) {
    streamBoxRefs.value[messageId] = el
    return
  }
  delete streamBoxRefs.value[messageId]
}

function scrollStreamBoxesToBottom() {
  for (const m of props.messages) {
    if (!m.streaming) continue
    const el = streamBoxRefs.value[m.id]
    if (!el) continue
    el.scrollTop = el.scrollHeight
  }
}

watch(
  () =>
    props.messages.map((m) => ({
      id: m.id,
      content: m.content,
      streamContent: m.streamContent,
      streaming: m.streaming,
      stepLabel: m.currentStep?.label,
      stepStatus: m.currentStep?.status,
      planSteps: m.planSteps?.map((s) => `${s.stepId}:${s.status}`).join('|')
    })),
  () => {
    void nextTick(() => {
      scrollToBottom()
      scrollStreamBoxesToBottom()
    })
  },
  { deep: true, immediate: true }
)
</script>

<template>
  <div ref="messageListRef" class="agent-chat__messages">
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
      <div class="agent-msg__body">
        <div class="agent-msg__bubble">{{ m.content }}</div>
        <div class="agent-msg__meta" v-if="m.role === 'assistant' && m.currentStep">
          <LoadingOutlined
            v-if="m.currentStep.status === 'running'"
            class="agent-msg__step-icon agent-msg__step-icon--spin"
          />
          <CheckCircleTwoTone v-else-if="m.currentStep.status === 'succeeded'" two-tone-color="#52c41a" />
          <CloseCircleTwoTone v-else-if="m.currentStep.status === 'failed'" two-tone-color="#ff4d4f" />
          <span class="agent-msg__step-text">当前步骤：{{ m.currentStep.label }}</span>
          <a-button
            v-if="!m.streaming && m.content.includes('结果请查看输出区')"
            type="link"
            size="small"
            class="agent-msg__view-output-btn"
            @click="emit('show-output')"
          >
            查看结果
          </a-button>
        </div>
        <div v-if="m.role === 'assistant' && m.planSteps?.length" class="agent-msg__plan">
          <div class="agent-msg__plan-title">执行步骤</div>
          <div
            v-for="step in m.planSteps"
            :key="step.stepId"
            class="agent-msg__plan-item"
            :class="{
              'agent-msg__plan-item--running': step.status === 'running',
              'agent-msg__plan-item--done': step.status === 'succeeded',
              'agent-msg__plan-item--failed': step.status === 'failed'
            }"
          >
            <LoadingOutlined v-if="step.status === 'running'" class="agent-msg__step-icon--spin" />
            <CheckCircleTwoTone v-else-if="step.status === 'succeeded'" two-tone-color="#52c41a" />
            <CloseCircleTwoTone v-else-if="step.status === 'failed'" two-tone-color="#ff4d4f" />
            <span v-else class="agent-msg__plan-dot" />
            <span>{{ step.label }}</span>
          </div>
        </div>
        <div
          v-if="m.role === 'assistant' && m.streaming && m.streamContent"
          :ref="(el) => setStreamBoxRef(m.id, el)"
          class="agent-msg__stream"
        >
          {{ m.streamContent }}
        </div>
      </div>
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

  .agent-msg__body {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .agent-msg__bubble {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
  }
}

.agent-msg__avatar {
  flex-shrink: 0;
}

.agent-msg__body {
  width: 85%;
  min-width: 0;
}

.agent-msg__bubble {
  display: inline-block;
  width: fit-content;
  max-width: 100%;
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

.agent-msg__meta {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8c8c8c;
  font-size: 12px;
}

.agent-msg__view-output-btn {
  margin-left: 4px;
  padding: 0;
  height: auto;
  line-height: 1;
  font-size: 12px;
}

.agent-msg__step-icon--spin {
  animation: agent-spin 1s linear infinite;
}

.agent-msg__stream {
  margin-top: 8px;
  height: 180px;
  overflow: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fff;
  padding: 10px 12px;
  color: #434343;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.agent-msg__plan {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
}

.agent-msg__plan-title {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.agent-msg__plan-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #595959;
  line-height: 1.8;
}

.agent-msg__plan-item--running {
  color: #1677ff;
}

.agent-msg__plan-item--done {
  color: #389e0d;
}

.agent-msg__plan-item--failed {
  color: #cf1322;
}

.agent-msg__plan-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
}

.agent-msg__stream::-webkit-scrollbar {
  display: none;
}

@keyframes agent-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
