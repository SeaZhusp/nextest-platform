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
  /** 底部输入区限制最大宽度并居中（新建会话与历史会话一致） */
  narrowMaxWidth?: boolean
}>()

const inputText = defineModel<string>('inputText', { default: '' })
const selectedProfileId = defineModel<number | null>('selectedProfileId', { default: null })
const temperature = defineModel<number>('temperature', { default: 0.7 })

const emit = defineEmits<{
  send: []
  stop: []
  'skill-change': [skillId: string]
}>()

const { skillPopoverOpen, modelPopoverOpen, tempPopoverOpen } = useComposerPopovers()

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
  <footer
    class="agent-chat__composer-outer"
    :class="{ 'agent-chat__composer-outer--bounded': props.narrowMaxWidth }"
  >
    <div class="composer-card" :class="{ 'composer-card--pill': props.narrowMaxWidth }">
      <Textarea v-model="inputText" :disabled="sending" @send="onSend" />
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
        @stop="emit('stop')"
        @skill-pick="onSkillPick"
        @model-pick="onModelPick"
      />

      <ConfigTags
        :skill-label="currentSkillLabel"
        :model-label="currentModelLabel"
        :temperature-tag-text="temperatureTagText"
        :model-selected="selectedProfileId != null"
      />
    </div>
  </footer>
</template>

<style scoped lang="scss">
.agent-chat__composer-outer {
  padding: 12px 16px 16px;
  flex-shrink: 0;
}

.agent-chat__composer-outer--bounded {
  max-width: 800px;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
}

.composer-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.composer-card--pill {
  border-radius: 22px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.06);
}

.composer-card__divider {
  height: 1px;
  margin: 0 14px;
  background: #f0f0f0;
}
</style>

<style lang="scss">
.composer-pop-overlay .ant-popover-inner {
  padding: 8px 10px;
  border-radius: 10px;
  box-shadow:
    0 6px 16px 0 rgba(0, 0, 0, 0.08),
    0 3px 6px -4px rgba(0, 0, 0, 0.12),
    0 9px 28px 8px rgba(0, 0, 0, 0.05);
}
</style>
