<script setup lang="ts">
import { SendOutlined, StopOutlined } from '@ant-design/icons-vue'
import SvgIcon from '@/components/SvgIcon.vue'
import SkillSelect from './SkillSelect.vue'
import ModelSelect from './ModelSelect.vue'
import Temperature from './Temperature.vue'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'

defineProps<{
  selectedSkillId: string
  skillSelectOptions: { label: string; value: string }[]
  skillsLoading: boolean
  profiles: UserLlmProfileOut[]
  profilesLoading: boolean
  sending: boolean
  sendDisabled: boolean
}>()

const skillPopoverOpen = defineModel<boolean>('skillPopoverOpen', { default: false })
const modelPopoverOpen = defineModel<boolean>('modelPopoverOpen', { default: false })
const tempPopoverOpen = defineModel<boolean>('tempPopoverOpen', { default: false })
const selectedProfileId = defineModel<number | null>('selectedProfileId', { default: null })
const temperature = defineModel<number>('temperature', { default: 0.7 })

const emit = defineEmits<{
  send: []
  stop: []
  'skill-pick': [skillId: string]
  'model-pick': [profileId: number]
}>()

function onSkillPicked(id: string) {
  emit('skill-pick', id)
  skillPopoverOpen.value = false
}

function onModelPicked(id: number) {
  emit('model-pick', id)
  modelPopoverOpen.value = false
}
</script>

<template>
  <div class="composer-card__toolbar">
    <a-popover
      v-model:open="skillPopoverOpen"
      trigger="click"
      placement="topLeft"
      overlay-class-name="composer-pop-overlay"
    >
      <template #content>
        <SkillSelect
          :selected-skill-id="selectedSkillId"
          :options="skillSelectOptions"
          :loading="skillsLoading"
          @pick="onSkillPicked"
        />
      </template>
      <a-tooltip title="请选择技能">
        <a-button
          type="text"
          class="composer-icon-btn"
          :class="{ 'composer-icon-btn--active': skillPopoverOpen }"
        >
          <SvgIcon name="skill" :size="20" />
        </a-button>
      </a-tooltip>
    </a-popover>

    <a-popover
      v-model:open="modelPopoverOpen"
      trigger="click"
      placement="topLeft"
      overlay-class-name="composer-pop-overlay"
    >
      <template #content>
        <ModelSelect
          :selected-profile-id="selectedProfileId"
          :profiles="profiles"
          :profiles-loading="profilesLoading"
          @pick="onModelPicked"
        />
      </template>
      <a-tooltip title="请选择模型">
        <a-button
          type="text"
          class="composer-icon-btn"
          :class="{ 'composer-icon-btn--active': modelPopoverOpen }"
        >
          <SvgIcon name="llm" :size="20" />
        </a-button>
      </a-tooltip>
    </a-popover>

    <a-popover
      v-model:open="tempPopoverOpen"
      trigger="click"
      placement="topLeft"
      overlay-class-name="composer-pop-overlay"
    >
      <template #content>
        <Temperature v-model="temperature" />
      </template>
      <a-tooltip title="温度">
        <a-button
          type="text"
          class="composer-icon-btn"
          :class="{ 'composer-icon-btn--active': tempPopoverOpen }"
        >
          <SvgIcon name="temperature" :size="20" />
        </a-button>
      </a-tooltip>
    </a-popover>

    <div class="composer-card__spacer" />

    <a-tooltip :title="sending ? '停止生成' : sendDisabled ? '请先完成模型配置并选择模型' : '发送'">
      <a-button
        type="primary"
        shape="circle"
        class="composer-card__send"
        :disabled="sending ? false : sendDisabled"
        @click="sending ? emit('stop') : emit('send')"
      >
        <template #icon>
          <StopOutlined v-if="sending" />
          <SendOutlined v-else />
        </template>
      </a-button>
    </a-tooltip>
  </div>
</template>

<style scoped lang="scss">
.composer-card__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 6px 10px 4px 12px;
}

.composer-icon-btn {
  width: 40px;
  height: 40px;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  color: #595959;
  border-radius: 8px;

  &:hover {
    color: #1890ff;
    background: rgba(24, 144, 255, 0.06);
  }
}

.composer-icon-btn--active {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

.composer-card__spacer {
  flex: 1;
  min-width: 8px;
}

.composer-card__send {
  width: 40px !important;
  height: 40px !important;
  flex-shrink: 0;
  display: flex !important;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.35);
}
</style>
