<script setup lang="ts">
import type { AgentChatMessage } from '../../types'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import type { SkillMetaOut } from '@/schemas/skill'
import Welcome from './Welcome.vue'
import MessageList from './MessageList.vue'
import Composer from './Composer.vue'

defineProps<{
  selectedSkillId: string
  skills: SkillMetaOut[]
  skillsLoading: boolean
  messages: AgentChatMessage[]
  sending: boolean
  profiles: UserLlmProfileOut[]
  profilesLoading: boolean
}>()

const inputText = defineModel<string>('inputText', { default: '' })
const selectedProfileId = defineModel<number | null>('selectedProfileId', { default: null })
const temperature = defineModel<number>('temperature', { default: 0.7 })

const emit = defineEmits<{
  send: []
  'skill-change': [skillId: string]
  'show-output': []
}>()
</script>

<template>
  <section class="agent-chat">
    <Welcome v-if="messages.length === 0" />
    <MessageList :messages="messages" @show-output="emit('show-output')" />
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
      @send="emit('send')"
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
  background: #fafafa;
}

.agent-chat > :deep(.agent-chat__header),
.agent-chat > :deep(.agent-chat__welcome),
.agent-chat > :deep(.agent-chat__composer-outer) {
  flex-shrink: 0;
}
</style>
