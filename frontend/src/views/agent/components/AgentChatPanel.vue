<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  PlusOutlined,
  HistoryOutlined,
  RobotOutlined,
  SendOutlined,
  UnorderedListOutlined,
  CommentOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import type { AgentChatMessage } from '../types'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import type { SkillMetaOut } from '@/schemas/skill'
import LlmProviderIcon from '@/components/LlmProviderIcon.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { providerMeta } from '@/config/llmProviders'

const props = defineProps<{
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
  'new-session': []
  history: []
  'skill-change': [skillId: string]
}>()

const skillPopoverOpen = ref(false)
const modelPopoverOpen = ref(false)
const tempPopoverOpen = ref(false)

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

function onSkillPick(v: string | number) {
  emit('skill-change', String(v))
  skillPopoverOpen.value = false
}

function onModelPick(v: string | number) {
  const n = typeof v === 'number' ? v : Number(v)
  selectedProfileId.value = Number.isFinite(n) ? n : null
  modelPopoverOpen.value = false
}

function openSkillPopover() {
  modelPopoverOpen.value = false
  tempPopoverOpen.value = false
  skillPopoverOpen.value = true
}

function openModelPopover() {
  skillPopoverOpen.value = false
  tempPopoverOpen.value = false
  modelPopoverOpen.value = true
}

function openTempPopover() {
  skillPopoverOpen.value = false
  modelPopoverOpen.value = false
  tempPopoverOpen.value = true
}

watch(skillPopoverOpen, (open) => {
  if (open) {
    modelPopoverOpen.value = false
    tempPopoverOpen.value = false
  }
})

watch(modelPopoverOpen, (open) => {
  if (open) {
    skillPopoverOpen.value = false
    tempPopoverOpen.value = false
  }
})

watch(tempPopoverOpen, (open) => {
  if (open) {
    skillPopoverOpen.value = false
    modelPopoverOpen.value = false
  }
})

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

function onNewSession() {
  emit('new-session')
}

function onHistory() {
  emit('history')
}
</script>

<template>
  <section class="agent-chat">
    <header class="agent-chat__header">
      <div class="agent-chat__title">
        <RobotOutlined class="agent-chat__title-icon" />
        <span>测试智能体</span>
      </div>
      <div class="agent-chat__header-actions">
        <a-button type="text" size="small" title="新会话" @click="onNewSession">
          <PlusOutlined />
        </a-button>
        <a-button type="text" size="small" title="历史" @click="onHistory">
          <HistoryOutlined />
        </a-button>
      </div>
    </header>

    <div v-if="messages.length === 0" class="agent-chat__welcome">
      <RobotOutlined class="agent-chat__welcome-icon" />
      <ul class="agent-chat__features">
        <li><CommentOutlined /> 文档生成</li>
        <li><ThunderboltOutlined /> 多轮对话</li>
        <li><UnorderedListOutlined /> 持续优化</li>
      </ul>
      <p class="agent-chat__hint">
        平台不提供内置大模型。请点击右上角用户名 →「模型配置」添加 API 与密钥，再回到此处选择模型并生成用例。
      </p>
    </div>

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

    <footer class="agent-chat__composer-outer">
      <div class="composer-card">
        <a-textarea
          v-model:value="inputText"
          :bordered="false"
          :rows="4"
          :auto-size="{ minRows: 3, maxRows: 8 }"
          placeholder="描述您的需求，例如：帮我生成一个登录功能的测试用例…"
          class="composer-card__textarea"
          @pressEnter.exact.prevent="onSend"
        />
        <div class="composer-card__divider" />

        <div class="composer-card__toolbar">
          <a-popover
            v-model:open="skillPopoverOpen"
            trigger="click"
            placement="topLeft"
            overlay-class-name="composer-pop-overlay"
          >
            <template #content>
              <div class="composer-pop__body">
                <div class="composer-pop__title">选择技能</div>
                <a-select
                  :value="selectedSkillId"
                  show-search
                  :options="skillSelectOptions"
                  option-filter-prop="label"
                  class="composer-pop__select"
                  :loading="skillsLoading"
                  :dropdown-match-select-width="false"
                  :dropdown-style="{ minWidth: '260px', maxWidth: '360px' }"
                  popup-class-name="agent-chat-skill-dropdown"
                  placeholder="请选择技能"
                  @update:value="onSkillPick"
                />
              </div>
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
              <div class="composer-pop__body">
                <div class="composer-pop__title">选择模型</div>
                <a-select
                  :value="selectedProfileId"
                  class="composer-pop__select"
                  :loading="profilesLoading"
                  :disabled="profiles.length === 0 && !profilesLoading"
                  option-label-prop="label"
                  :dropdown-match-select-width="false"
                  :dropdown-style="{ minWidth: '260px', maxWidth: '360px' }"
                  popup-class-name="agent-chat-model-dropdown"
                  :placeholder="profiles.length === 0 ? '暂无模型配置' : '请选择模型'"
                  @update:value="onModelPick"
                >
                  <template #optionLabel="opt">
                    <span v-if="opt" class="composer-card__selection">
                      <LlmProviderIcon
                        v-if="opt.provider"
                        :meta="providerMeta(opt.provider)"
                        :size="18"
                      />
                      <span class="composer-card__selection-text">{{ opt.label }}</span>
                    </span>
                  </template>
                  <a-select-opt-group v-if="profiles.length" label="我的配置">
                    <a-select-option
                      v-for="p in profiles"
                      :key="p.id"
                      :value="p.id"
                      :label="p.display_name"
                      :provider="p.provider"
                    >
                      <div class="composer-card__opt">
                        <LlmProviderIcon :meta="providerMeta(p.provider)" :size="18" />
                        <span class="composer-card__opt-name">{{ p.display_name }}</span>
                        <a-tag color="success" class="composer-card__opt-tag">我的</a-tag>
                      </div>
                    </a-select-option>
                  </a-select-opt-group>
                </a-select>
              </div>
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
              <div class="agent-chat__temp-body">
                <div class="agent-chat__temp-title">温度 {{ temperature.toFixed(1) }}</div>
                <a-slider v-model:value="temperature" :min="0" :max="1" :step="0.1" />
                <div class="agent-chat__temp-hint">越高越随机，越低越稳定</div>
              </div>
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

          <a-tooltip :title="sendDisabled ? '请先完成模型配置并选择模型' : '发送'">
            <a-button
              type="primary"
              shape="circle"
              class="composer-card__send"
              :loading="sending"
              :disabled="sendDisabled"
              @click="onSend"
            >
              <template #icon>
                <SendOutlined />
              </template>
            </a-button>
          </a-tooltip>
        </div>

        <div class="composer-card__tags">
          <a-tag
            class="composer-tag"
            color="processing"
            @click="openSkillPopover"
          >
            {{ currentSkillLabel }}
          </a-tag>
          <a-tag
            class="composer-tag"
            :color="selectedProfileId != null ? 'blue' : 'warning'"
            @click="openModelPopover"
          >
            {{ currentModelLabel }}
          </a-tag>
          <a-tag class="composer-tag" @click="openTempPopover">
            {{ temperatureTagText }}
          </a-tag>
        </div>
      </div>
    </footer>
  </section>
</template>

<style lang="scss" scoped>
.agent-chat {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

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

.agent-chat__welcome {
  padding: 24px 16px;
  text-align: center;
  color: #8c8c8c;
}

.agent-chat__welcome-icon {
  font-size: 48px;
  color: #d9d9d9;
  margin-bottom: 12px;
}

.agent-chat__features {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  line-height: 2;
  text-align: left;
  max-width: 220px;
  margin-left: auto;
  margin-right: auto;
}

.agent-chat__hint {
  margin: 16px auto 0;
  max-width: 300px;
  font-size: 12px;
  line-height: 1.55;
  color: #bfbfbf;
}

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

.composer-card__textarea {
  padding: 14px 16px 8px;
  font-size: 14px;
  line-height: 1.55;
  resize: none;

  :deep(.ant-input) {
    padding: 0;
    box-shadow: none !important;
  }
}

.composer-card__divider {
  height: 1px;
  margin: 0 14px;
  background: #f0f0f0;
}

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

.composer-card__tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 0 12px 10px 12px;
}

.composer-tag {
  margin: 0 !important;
  max-width: 100%;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;

  &:hover {
    opacity: 0.92;
  }
}

.composer-pop__body {
  min-width: 240px;
}

.composer-pop__title {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.composer-pop__select {
  width: 280px;
  max-width: min(280px, 85vw);
}

.composer-card__selection {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
}

.composer-card__selection-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-card__opt {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.composer-card__opt-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-card__opt-tag {
  margin: 0 !important;
  flex-shrink: 0;
  font-size: 11px;
  line-height: 18px;
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

.agent-chat__temp-body {
  width: 220px;
}

.agent-chat__temp-title {
  font-size: 13px;
  margin-bottom: 8px;
  color: #262626;
}

.agent-chat__temp-hint {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 4px;
}
</style>
