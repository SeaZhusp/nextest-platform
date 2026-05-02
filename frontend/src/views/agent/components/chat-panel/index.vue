<script setup lang="ts">
import type { AgentChatMessage } from '../../types'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import type { SkillMetaOut } from '@/schemas/skill'
import Welcome from './Welcome.vue'
import MessageList from './MessageList.vue'
import Composer from './Composer.vue'

withDefaults(
  defineProps<{
    selectedSkillId: string
    skills: SkillMetaOut[]
    skillsLoading: boolean
    messages: AgentChatMessage[]
    sending: boolean
    profiles: UserLlmProfileOut[]
    profilesLoading: boolean
    /** 载入历史会话时仅遮住消息列表区域，不遮输入区 */
    historySessionLoading?: boolean
  }>(),
  { historySessionLoading: false }
)

const inputText = defineModel<string>('inputText', { default: '' })
const selectedProfileId = defineModel<number | null>('selectedProfileId', { default: null })
const temperature = defineModel<number>('temperature', { default: 0.7 })

const emit = defineEmits<{
  send: []
  stop: []
  'skill-change': [skillId: string]
  'show-output': []
  'apply-prompt': [text: string]
}>()
</script>

<template>
  <section class="agent-chat">
    <div class="agent-chat__messages-area">
      <template v-if="!historySessionLoading">
        <Welcome v-if="messages.length === 0" @apply-prompt="emit('apply-prompt', $event)" />
        <MessageList v-else :messages="messages" @show-output="emit('show-output')" />
      </template>
      <div
        v-if="historySessionLoading"
        class="agent-chat__history-loading"
        aria-busy="true"
        aria-live="polite"
      >
        <a-spin size="large" />
      </div>
    </div>
    <Composer
      v-model:input-text="inputText"
      v-model:selected-profile-id="selectedProfileId"
      v-model:temperature="temperature"
      :selected-skill-id="selectedSkillId"
      :skills="skills"
      :skills-loading="skillsLoading"
      :sending="sending"
      :profiles="profiles"
      :profiles-loading="profilesLoading"
      narrow-max-width
      @send="emit('send')"
      @stop="emit('stop')"
      @skill-change="emit('skill-change', $event)"
    />
  </section>
</template>

<style scoped lang="scss">
.agent-chat {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f7f8fa;
}

.agent-chat__messages-area {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.agent-chat__messages-area > :deep(.agent-chat__welcome),
.agent-chat__messages-area > :deep(.agent-chat__messages) {
  flex: 1;
  min-height: 0;
}

.agent-chat__history-loading {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f8fa;
  box-sizing: border-box;
}

.agent-chat > :deep(.agent-chat__composer-outer) {
  flex-shrink: 0;
}
</style>
