<script setup lang="ts">
import { computed } from 'vue'
import type { SkillMetaOut } from '@/schemas/skill'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import { useComposerPopovers } from './useComposerPopovers'
import Textarea from './composer/Textarea.vue'
import ToolRow from './composer/ToolRow.vue'
import ConfigTags from './composer/ConfigTags.vue'

const props = defineProps<{
  selectedSkillId: string
  skills: SkillMetaOut[]
  skillsLoading: boolean
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
}>()

const {
  skillPopoverOpen,
  modelPopoverOpen,
  tempPopoverOpen,
  openSkillPopover,
  openModelPopover,
  openTempPopover
} = useComposerPopovers()

const skillSelectOptions = computed(() => {
  const base = props.skills.map((s) => ({
    label: s.name && s.name.trim() ? s.name.trim() : '未命名技能',
    value: s.skill_id
  }))
  const cur = props.selectedSkillId?.trim() || 'test_case_gen'
  if (!base.some((o) => o.value === cur)) {
    return [{ label: '当前技能（列表未同步）', value: cur }, ...base]
  }
  if (!base.length) {
    return [{ label: '测试用例生成', value: 'test_case_gen' }]
  }
  return base
})

const currentSkillLabel = computed(() => {
  const sid = props.selectedSkillId?.trim() || 'test_case_gen'
  const row = props.skills.find((s) => s.skill_id === sid)
  if (row) {
    return row.name?.trim() ? row.name.trim() : '未命名技能'
  }
  return '当前技能（列表未同步）'
})

const currentModelLabel = computed(() => {
  if (selectedProfileId.value == null) return '请选择模型'
  const p = props.profiles.find((x) => x.id === selectedProfileId.value)
  return p?.display_name ?? '请选择模型'
})

const temperatureTagText = computed(() => `温度 ${temperature.value.toFixed(1)}`)

const sendDisabled = computed(
  () =>
    props.sending ||
    props.profilesLoading ||
    props.profiles.length === 0 ||
    selectedProfileId.value == null
)

function onSend() {
  emit('send')
}

function onSkillPick(skillId: string) {
  emit('skill-change', skillId)
}

function onModelPick(profileId: number) {
  selectedProfileId.value = profileId
}
</script>

<template>
  <footer class="agent-chat__composer-outer">
    <div class="composer-card">
      <Textarea v-model="inputText" @send="onSend" />
      <div class="composer-card__divider" />

      <ToolRow
        v-model:skill-popover-open="skillPopoverOpen"
        v-model:model-popover-open="modelPopoverOpen"
        v-model:temp-popover-open="tempPopoverOpen"
        v-model:selected-profile-id="selectedProfileId"
        v-model:temperature="temperature"
        :selected-skill-id="selectedSkillId"
        :skill-select-options="skillSelectOptions"
        :skills-loading="skillsLoading"
        :profiles="profiles"
        :profiles-loading="profilesLoading"
        :sending="sending"
        :send-disabled="sendDisabled"
        @send="onSend"
        @skill-pick="onSkillPick"
        @model-pick="onModelPick"
      />

      <ConfigTags
        :skill-label="currentSkillLabel"
        :model-label="currentModelLabel"
        :temperature-tag-text="temperatureTagText"
        :model-selected="selectedProfileId != null"
        @open-skill="openSkillPopover"
        @open-model="openModelPopover"
        @open-temp="openTempPopover"
      />
    </div>
  </footer>
</template>

<style scoped lang="scss">
.agent-chat__composer-outer {
  padding: 12px 16px 16px;
  flex-shrink: 0;
}

.composer-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.composer-card__divider {
  height: 1px;
  margin: 0 14px;
  background: #f0f0f0;
}
</style>

<style lang="scss">
.agent-chat-model-dropdown.ant-select-dropdown {
  min-width: 260px !important;
  max-width: 360px !important;
}

.agent-chat-skill-dropdown.ant-select-dropdown {
  min-width: 220px !important;
  max-width: 340px !important;
}

.composer-pop-overlay .ant-popover-inner {
  padding: 12px 14px;
}
</style>
