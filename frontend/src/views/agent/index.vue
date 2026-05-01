<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { getAgentSessionMessages, postAgentChatStream } from '@/api/agent'
import { listUserLlmProfiles } from '@/api/userLlmProfiles'
import type { AgentStreamDonePayload } from '@/schemas/agent'
import type { SkillMetaOut } from '@/schemas/skill'
import { listSkills } from '@/api/skills'
import {
  buildTextParts,
  validatePhase1UserInput,
  type AgentHistoryMessageOut
} from '@/schemas/agent'
import type { TestCaseItem } from '@/schemas/testcase'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import AgentOutputPanel from './components/AgentOutputPanel.vue'
import AgentChatPanel from './components/chat-panel/index.vue'
import type { AgentChatMessage, AgentOutputTabKey } from './types'

const route = useRoute()

/** 当前请求使用的技能（与输入区选择一致）；默认测试用例生成 */
const selectedSkillId = ref('test_case_gen')

const registeredSkills = ref<SkillMetaOut[]>([])
const skillsLoading = ref(false)

async function loadRegisteredSkills() {
  skillsLoading.value = true
  try {
    const res = await listSkills()
    registeredSkills.value = res.data ?? []
  } catch {
    registeredSkills.value = []
  } finally {
    skillsLoading.value = false
  }
}

function applySkillId(next: string) {
  const sid = next.trim() || 'test_case_gen'
  selectedSkillId.value = sid
}

const mockMessages = ref<AgentChatMessage[]>([])

const inputText = ref('')
const sessionId = ref<string | null>(null)
const sending = ref(false)
const outputTab = ref<AgentOutputTabKey>('table')

const llmProfiles = ref<UserLlmProfileOut[]>([])
const profilesLoading = ref(false)
const selectedProfileId = ref<number | null>(null)
const temperature = ref(0.7)

const tableColumns = [
  { title: '编号', dataIndex: 'case_no', key: 'case_no', width: 110, ellipsis: true },
  { title: '模块', dataIndex: 'module', key: 'module', width: 90 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '前置条件', dataIndex: 'preconditions', key: 'preconditions', ellipsis: true },
  { title: '步骤', dataIndex: 'steps', key: 'steps', ellipsis: true },
  { title: '预期', dataIndex: 'expected', key: 'expected', ellipsis: true },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 }
]

function rowsFromTestCases(items: TestCaseItem[]) {
  return items.map((c, i) => ({
    key: c.case_no || String(i),
    case_no: c.case_no,
    module: c.module,
    title: c.title,
    preconditions: c.preconditions ?? '',
    steps: c.steps ?? '',
    expected: c.expected ?? '',
    priority: c.priority ?? 'P2'
  }))
}

const mockTestCases = ref<
  {
    key: string
    case_no: string
    module: string
    title: string
    preconditions: string
    steps: string
    expected: string
    priority: string
  }[]
>([])

const editorJsonText = ref('[]')

const markdownReport = ref(`# 测试用例报告

在右侧对话中输入需求并发送后，将在此展示 Markdown 报告（可后续接入导出）。
`)

async function loadLlmProfiles() {
  profilesLoading.value = true
  try {
    const res = await listUserLlmProfiles({ active_only: true })
    const items = res.data?.items ?? []
    llmProfiles.value = items
    if (selectedProfileId.value != null && !items.some((x) => x.id === selectedProfileId.value)) {
      selectedProfileId.value = null
    }
    if (selectedProfileId.value == null && items.length > 0) {
      selectedProfileId.value = items[0].id
    }
  } catch {
    llmProfiles.value = []
  } finally {
    profilesLoading.value = false
  }
}

watch(
  () => route.path,
  (p) => {
    if (p === '/agent') {
      void loadLlmProfiles()
      void loadRegisteredSkills()
    }
  },
  { immediate: true }
)

function buildStreamSummary(data: AgentStreamDonePayload) {
  const n = data.test_cases.length
  const tpl = data.used_template ? '（未选择模型配置或未传 Key，为模板用例）' : ''
  return `技能「${data.skill_id}」已完成，共 ${n} 条用例。会话：${data.session_id} ${tpl}`.trim()
}

async function handleSend() {
  const t = inputText.value.trim()
  if (!t) return

  if (selectedProfileId.value == null) {
    message.warning('请先在右上角用户菜单「模型配置」中添加并选择大模型')
    return
  }

  const parts = buildTextParts(t)
  const v = validatePhase1UserInput(parts)
  if (!v.ok) {
    message.warning(v.message)
    return
  }

  mockMessages.value.push({
    id: String(Date.now()),
    role: 'user',
    content: t
  })

  const assistId = String(Date.now() + 1)
  const assistIdx = mockMessages.value.length
  mockMessages.value.push({
    id: assistId,
    role: 'assistant',
    content: '正在生成… 模型流式输出在左侧「编辑器」中实时显示。'
  })

  sending.value = true
  inputText.value = ''
  editorJsonText.value = ''
  let streamBuf = ''

  try {
    await postAgentChatStream(
      {
        session_id: sessionId.value ?? undefined,
        skill_id: selectedSkillId.value || 'test_case_gen',
        parts,
        llm_profile_id: selectedProfileId.value,
        temperature: temperature.value
      },
      {
        onToken: (text) => {
          streamBuf += text
          editorJsonText.value = streamBuf
          outputTab.value = 'editor'
        },
        onDone: (data) => {
          sessionId.value = data.session_id
          if (data.test_cases?.length) {
            const rows = rowsFromTestCases(data.test_cases)
            mockTestCases.value = rows
            editorJsonText.value = JSON.stringify(rows, null, 2)
            outputTab.value = 'table'
          }
          mockMessages.value[assistIdx].content = buildStreamSummary(data)
        },
        onError: (msg, details) => {
          const reason =
            details &&
            typeof details === 'object' &&
            details !== null &&
            'reason' in details &&
            String((details as { reason?: unknown }).reason || '').trim()
              ? String((details as { reason: string }).reason)
              : ''
          const full = reason ? `${msg}（${reason}）` : msg
          message.error(full)
          mockMessages.value[assistIdx].content = `生成失败：${full}`
        }
      }
    )
  } catch {
    // fetch 非 2xx 或 onError 已提示
  } finally {
    sending.value = false
  }
}

function handleSave() {
  console.info('save', editorJsonText.value)
}

function resetSessionForSkillSwitch() {
  sessionId.value = null
  mockMessages.value = []
  mockTestCases.value = []
  editorJsonText.value = '[]'
  outputTab.value = 'table'
}

async function handleNewSession() {
  resetSessionForSkillSwitch()
  let skillHint = ''
  if (registeredSkills.value.length) {
    skillHint = ` 已注册技能：${registeredSkills.value.map((s) => s.skill_id).join(', ')}。`
  } else {
    skillHint = ' 当前无已注册技能。'
  }
  message.info(`已新建会话。${skillHint}`)
}

function handleSkillChange(nextSkillId: string) {
  const next = (nextSkillId || 'test_case_gen').trim() || 'test_case_gen'
  if (next === selectedSkillId.value) return
  if (!sessionId.value) {
    applySkillId(next)
    return
  }
  Modal.confirm({
    title: '切换技能',
    content: '切换技能将结束当前会话并清空对话与输出区已有结果，是否继续？',
    okText: '确认切换',
    cancelText: '取消',
    onOk() {
      resetSessionForSkillSwitch()
      applySkillId(next)
      message.success('已切换技能，请在新会话中继续对话')
    }
  })
}

/** 从路由 ?skill= 同步（与手动切换同一套确认逻辑） */
function syncSkillFromRoute(skillFromQuery: string | null) {
  if (!skillFromQuery?.trim()) return
  const next = skillFromQuery.trim()
  if (next === selectedSkillId.value) return
  if (!sessionId.value) {
    applySkillId(next)
    return
  }
  Modal.confirm({
    title: '切换技能',
    content:
      '路由指定了其他技能。切换技能将结束当前会话并清空对话与输出区已有结果，是否继续？',
    okText: '确认切换',
    cancelText: '取消',
    onOk() {
      resetSessionForSkillSwitch()
      applySkillId(next)
      message.success('已切换技能，请在新会话中继续对话')
    }
  })
}

watch(
  () => route.query.skill,
  (s) => {
    const q = typeof s === 'string' && s.trim() ? s.trim() : null
    syncSkillFromRoute(q)
  },
  { immediate: true }
)

function userTextFromApiMessage(content: Record<string, unknown>): string {
  const parts = content.parts
  if (!Array.isArray(parts)) return ''
  return parts
    .map((p) => (p && typeof p === 'object' ? (p as { type?: string; text?: string }) : null))
    .filter((p): p is { type?: string; text?: string } => !!p)
    .filter((p) => p.type === 'text' && typeof p.text === 'string')
    .map((p) => p.text)
    .join('\n')
    .trim()
}

function assistantBriefFromApiMessage(content: Record<string, unknown>): string {
  const text = typeof content.text === 'string' ? content.text : ''
  if (!text) return '[助手回复]'
  if (text.length > 360) return `${text.slice(0, 360)}…`
  return text
}

function tryHydrateTestCasesFromHistory(messages: AgentHistoryMessageOut[]): void {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i]
    if (m.role !== 'assistant') continue
    const raw = m.content_json?.text
    const text = typeof raw === 'string' ? raw : ''
    if (!text.trim()) continue
    try {
      const parsed = JSON.parse(text) as unknown
      if (
        Array.isArray(parsed) &&
        parsed.length &&
        parsed.every((x) => x && typeof x === 'object')
      ) {
        mockTestCases.value = rowsFromTestCases(parsed as TestCaseItem[])
        editorJsonText.value = JSON.stringify(mockTestCases.value, null, 2)
        outputTab.value = 'table'
        return
      }
    } catch {
      /* 非 JSON 或结构不符 */
    }
  }
  mockTestCases.value = []
  editorJsonText.value = '[]'
  outputTab.value = 'editor'
}

async function onSelectHistorySession(payload: { sessionId: string; skillId: string }) {
  const { sessionId: sid, skillId } = payload
  try {
    const res = await getAgentSessionMessages(sid)
    const data = res.data
    if (!data) {
      message.warning('未拉取到会话数据')
      return
    }
    sessionId.value = data.session_id
    applySkillId((skillId || data.skill_id || 'test_case_gen').trim() || 'test_case_gen')
    mockMessages.value = data.messages.map((m) => ({
      id: String(m.id),
      role: m.role,
      content:
        m.role === 'user'
          ? userTextFromApiMessage(m.content_json as Record<string, unknown>)
          : assistantBriefFromApiMessage(m.content_json as Record<string, unknown>)
    }))
    tryHydrateTestCasesFromHistory(data.messages)
    message.success('已载入历史会话')
  } catch {
    /* request 拦截器已提示 */
  }
}

/** 输出区与对话区之间的可拖拽分隔（对话区固定宽度，输出区占满剩余） */
const AGENT_CHAT_WIDTH_KEY = 'agent_chat_panel_width'
const CHAT_PANEL_MIN = 280
const OUTPUT_PANEL_MIN = 260
const RESIZER_WIDTH = 6
const DEFAULT_CHAT_WIDTH = 400

const agentBodyRef = ref<HTMLElement | null>(null)
const chatPanelWidthPx = ref(DEFAULT_CHAT_WIDTH)
const resizeDragging = ref(false)
let resizeStartX = 0
let resizeStartW = 0

function clampChatWidth(w: number, bodyWidth: number): number {
  const maxChat = Math.max(CHAT_PANEL_MIN, bodyWidth - OUTPUT_PANEL_MIN - RESIZER_WIDTH)
  return Math.round(Math.min(maxChat, Math.max(CHAT_PANEL_MIN, w)))
}

function readStoredChatWidth(): void {
  try {
    const raw = localStorage.getItem(AGENT_CHAT_WIDTH_KEY)
    const n = raw ? Number(raw) : NaN
    if (Number.isFinite(n) && n >= CHAT_PANEL_MIN) {
      chatPanelWidthPx.value = n
    }
  } catch {
    /* ignore */
  }
}

function onResizePointerMove(clientX: number) {
  if (!resizeDragging.value || !agentBodyRef.value) return
  const bodyW = agentBodyRef.value.getBoundingClientRect().width
  const delta = clientX - resizeStartX
  /* 向右拖 = 分隔条右移 = 对话区变窄；向左拖 = 对话区变宽 */
  chatPanelWidthPx.value = clampChatWidth(resizeStartW - delta, bodyW)
}

function onResizePointerUp() {
  if (!resizeDragging.value) return
  resizeDragging.value = false
  document.body.style.removeProperty('cursor')
  document.body.style.removeProperty('user-select')
  try {
    localStorage.setItem(AGENT_CHAT_WIDTH_KEY, String(chatPanelWidthPx.value))
  } catch {
    /* ignore */
  }
}

function onResizeMouseMove(e: MouseEvent) {
  onResizePointerMove(e.clientX)
}

function onResizeMouseUp() {
  onResizePointerUp()
}

function onResizeTouchMove(e: TouchEvent) {
  if (!resizeDragging.value) return
  e.preventDefault()
  const t = e.touches[0]
  if (t) onResizePointerMove(t.clientX)
}

function onResizeTouchEnd() {
  onResizePointerUp()
}

function onResizeStart(e: MouseEvent) {
  e.preventDefault()
  resizeDragging.value = true
  resizeStartX = e.clientX
  resizeStartW = chatPanelWidthPx.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeTouchStart(e: TouchEvent) {
  const t = e.touches[0]
  if (!t) return
  e.preventDefault()
  resizeDragging.value = true
  resizeStartX = t.clientX
  resizeStartW = chatPanelWidthPx.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeKeydown(e: KeyboardEvent) {
  if (!agentBodyRef.value) return
  const bodyW = agentBodyRef.value.getBoundingClientRect().width
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    chatPanelWidthPx.value = clampChatWidth(chatPanelWidthPx.value + 16, bodyW)
    try {
      localStorage.setItem(AGENT_CHAT_WIDTH_KEY, String(chatPanelWidthPx.value))
    } catch {
      /* ignore */
    }
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    chatPanelWidthPx.value = clampChatWidth(chatPanelWidthPx.value - 16, bodyW)
    try {
      localStorage.setItem(AGENT_CHAT_WIDTH_KEY, String(chatPanelWidthPx.value))
    } catch {
      /* ignore */
    }
  }
}

function applyChatWidthToBody() {
  if (!agentBodyRef.value) return
  const bodyW = agentBodyRef.value.getBoundingClientRect().width
  chatPanelWidthPx.value = clampChatWidth(chatPanelWidthPx.value, bodyW)
}

onMounted(() => {
  readStoredChatWidth()
  requestAnimationFrame(() => applyChatWidthToBody())
  window.addEventListener('mousemove', onResizeMouseMove)
  window.addEventListener('mouseup', onResizeMouseUp)
  window.addEventListener('touchmove', onResizeTouchMove, { passive: false })
  window.addEventListener('touchend', onResizeTouchEnd)
  window.addEventListener('touchcancel', onResizeTouchEnd)
  window.addEventListener('resize', applyChatWidthToBody)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onResizeMouseMove)
  window.removeEventListener('mouseup', onResizeMouseUp)
  window.removeEventListener('touchmove', onResizeTouchMove)
  window.removeEventListener('touchend', onResizeTouchEnd)
  window.removeEventListener('touchcancel', onResizeTouchEnd)
  window.removeEventListener('resize', applyChatWidthToBody)
  document.body.style.removeProperty('cursor')
  document.body.style.removeProperty('user-select')
})
</script>

<template>
  <div class="agent-page">
    <div
      ref="agentBodyRef"
      class="agent-body"
      :class="{ 'agent-body--resizing': resizeDragging }"
    >
      <div class="agent-body__output">
        <AgentOutputPanel
          v-model:editor-json="editorJsonText"
          v-model:output-tab="outputTab"
          :session-id="sessionId"
          :table-columns="tableColumns"
          :rows="mockTestCases"
          :markdown-report="markdownReport"
          @save="handleSave"
        />
      </div>
      <div
        class="agent-body__resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label="拖动调节输出区与对话区宽度"
        tabindex="0"
        @mousedown="onResizeStart"
        @touchstart.prevent="onResizeTouchStart"
        @keydown="onResizeKeydown"
      />
      <div class="agent-body__chat" :style="{ width: `${chatPanelWidthPx}px` }">
        <AgentChatPanel
          v-model:input-text="inputText"
          v-model:selected-profile-id="selectedProfileId"
          v-model:temperature="temperature"
          :selected-skill-id="selectedSkillId"
          :skills="registeredSkills"
          :skills-loading="skillsLoading"
          :messages="mockMessages"
          :sending="sending"
          :profiles="llmProfiles"
          :profiles-loading="profilesLoading"
          @send="handleSend"
          @new-session="handleNewSession"
          @select-history-session="onSelectHistorySession"
          @skill-change="handleSkillChange"
        />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
/* 与主布局 content 的 marginTop + padding 对齐，避免整页被对话撑高，滚动留在对话区内 */
.agent-page {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 128px);
  max-height: calc(100vh - 128px);
  min-height: 0;
  overflow: hidden;
}

.agent-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 0;
  min-height: 0;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  background: #fff;
}

.agent-body__output {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.agent-body__resizer {
  flex-shrink: 0;
  width: 6px;
  margin: 0 -1px;
  cursor: col-resize;
  touch-action: none;
  background: #e8e8e8;
  align-self: stretch;
  position: relative;
  z-index: 2;
  transition: background 0.12s ease;

  &:hover {
    background: #bae0ff;
  }
}

.agent-body--resizing .agent-body__resizer {
  background: #1890ff;
}

.agent-body__chat {
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}
</style>
