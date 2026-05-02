<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  AGENT_ACTIVE_SESSION_CHANGED,
  AGENT_SIDEBAR_NEW_SESSION,
  AGENT_SIDEBAR_OPEN_SESSION,
  type AgentActiveSessionDetail,
  type AgentSidebarOpenSessionDetail,
} from '@/constants/agentSidebarBridge'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  getAgentSessionExportExcel,
  getAgentSessionMessages,
  patchAgentSessionLatestEditedOutput,
  patchAgentSessionRestoreLatestRawOutput,
  postAgentChatStream
} from '@/api/agent'
import { listUserLlmProfiles } from '@/api/userLlmProfiles'
import type { SkillMetaOut } from '@/schemas/skill'
import { listSkills } from '@/api/skills'
import {
  buildTextParts,
  validatePhase1UserInput,
  type AgentHistoryMessageOut,
  type AgentStreamPlanPayload,
  type AgentStreamStepPayload,
} from '@/schemas/agent'
import type { TestCaseItem } from '@/schemas/testcase'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import OutputPanel from './components/OutputPanel.vue'
import AgentChatPanel from './components/chat-panel/index.vue'
import WorkbenchHeader from './components/WorkbenchHeader.vue'
import type { AgentChatMessage, AgentOutputTabKey, DocumentModel, MindmapNode } from './types'

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
    syncRenderConfigForSkill(selectedSkillId.value)
  } catch {
    registeredSkills.value = []
    syncRenderConfigForSkill(selectedSkillId.value)
  } finally {
    skillsLoading.value = false
  }
}

function applySkillId(next: string) {
  const sid = next.trim() || 'test_case_gen'
  selectedSkillId.value = sid
  syncRenderConfigForSkill(sid)
}

const mockMessages = ref<AgentChatMessage[]>([])

const workbenchTitle = computed(() =>
  mockMessages.value.length === 0 ? '新对话' : '测试助手'
)

const inputText = ref('')

function applyWelcomePrompt(text: string) {
  inputText.value = text
}

const sessionId = ref<string | null>(null)
/** 从侧边栏打开历史会话时，在主内容区展示骨架屏，不用全局 success 提示 */
const historySessionLoading = ref(false)
const sending = ref(false)
const activeStreamAbort = ref<AbortController | null>(null)
const outputTab = ref<AgentOutputTabKey>('table')
const canRestoreRaw = ref(false)
const renderModes = ref<AgentOutputTabKey[]>(['table'])
const defaultRender = ref<AgentOutputTabKey>('table')

function normalizeRenderModes(modes: unknown): AgentOutputTabKey[] {
  if (!Array.isArray(modes)) return ['table']
  const out = modes.filter(
    (m): m is AgentOutputTabKey => m === 'table' || m === 'markdown' || m === 'mindmap'
  )
  return out.length ? out : ['table']
}

function syncRenderConfigForSkill(skillId: string): void {
  const meta = registeredSkills.value.find((s) => s.skill_id === skillId)
  const modes = normalizeRenderModes(meta?.render_modes)
  renderModes.value = modes
  const d = meta?.default_render
  defaultRender.value =
    d === 'table' || d === 'markdown' || d === 'mindmap'
      ? (d as AgentOutputTabKey)
      : modes[0] || 'table'
  if (!renderModes.value.includes(outputTab.value)) {
    outputTab.value = defaultRender.value
  }
}

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
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '操作', dataIndex: 'actions', key: 'actions', width: 64 }
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

function buildMarkdownFromRows(rows: DocumentModel['tableRows']): string {
  if (!rows.length) {
    return '# 测试用例报告\n\n暂无用例。'
  }
  const lines = ['# 测试用例报告', '', '| 编号 | 模块 | 标题 | 优先级 |', '| --- | --- | --- | --- |']
  for (const row of rows) {
    lines.push(`| ${row.case_no} | ${row.module} | ${row.title} | ${row.priority} |`)
  }
  return lines.join('\n')
}

function buildMindmapFromRows(rows: DocumentModel['tableRows']): MindmapNode[] {
  const map = new Map<string, MindmapNode>()
  for (const row of rows) {
    const group = row.module || '未分组'
    if (!map.has(group)) {
      map.set(group, { key: `module_${group}`, title: group, children: [] })
    }
    map.get(group)!.children!.push({
      key: `case_${row.key}`,
      title: `${row.case_no} ${row.title}`.trim(),
      children: []
    })
  }
  return [...map.values()]
}

function normalizeDocumentPayload(payload: unknown): DocumentModel {
  const p = payload && typeof payload === 'object' ? (payload as Partial<DocumentModel>) : {}
  const rows = Array.isArray(p.tableRows) ? (p.tableRows as DocumentModel['tableRows']) : []
  const markdown = typeof p.markdown === 'string' ? p.markdown : buildMarkdownFromRows(rows)
  const mindmap = Array.isArray(p.mindmap) ? (p.mindmap as MindmapNode[]) : buildMindmapFromRows(rows)
  const sync = p.sync ?? {
    revision: 0,
    lastEditedBy: 'system',
    lastEditedAt: Date.now()
  }
  return { tableRows: rows, markdown, mindmap, sync }
}

const panelDocument = ref<DocumentModel>({
  tableRows: [],
  markdown: `# 测试用例报告

在右侧对话中输入需求并发送后，将在此展示 Markdown 报告（可后续接入导出）。`,
  mindmap: [],
  sync: {
    revision: 0,
    lastEditedBy: 'system',
    lastEditedAt: Date.now()
  }
})

let syncGuard = false

watch(
  () => panelDocument.value.tableRows,
  (rows) => {
    if (syncGuard) return
    if (panelDocument.value.sync.lastEditedBy !== 'table') return
    syncGuard = true
    panelDocument.value.mindmap = buildMindmapFromRows(rows)
    panelDocument.value.markdown = buildMarkdownFromRows(rows)
    panelDocument.value.sync.revision += 1
    panelDocument.value.sync.lastEditedBy = 'system'
    panelDocument.value.sync.lastEditedAt = Date.now()
    syncGuard = false
  },
  { deep: true }
)

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
    content: '正在生成，请稍候…',
    streamContent: '',
    streaming: true,
    currentStep: null,
    planSteps: []
  })

  sending.value = true
  inputText.value = ''
  const abortController = new AbortController()
  activeStreamAbort.value = abortController

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
        onPlan: (plan: AgentStreamPlanPayload) => {
          const msg = mockMessages.value[assistIdx]
          if (!msg) return
          msg.planSteps = sortPlanSteps(
            (plan.steps || []).map((s) => ({
              stepId: s.step_id,
              label: s.label || s.step_id,
              status: 'pending'
            }))
          )
        },
        onToken: (text) => {
          const msg = mockMessages.value[assistIdx]
          if (!msg) return
          msg.streamContent = `${msg.streamContent || ''}${text}`
        },
        onStep: (step: AgentStreamStepPayload) => {
          const msg = mockMessages.value[assistIdx]
          if (!msg) return
          if (Array.isArray(msg.planSteps) && msg.planSteps.length) {
            const target = msg.planSteps.find((s) => s.stepId === step.step_id)
            if (target) {
              target.status = step.status
            } else {
              msg.planSteps.push({
                stepId: step.step_id,
                label: step.label || step.step_id,
                status: step.status
              })
            }
            msg.planSteps = sortPlanSteps(msg.planSteps)
          }
          msg.currentStep = {
            stepId: step.step_id,
            label: step.label,
            status: step.status
          }
        },
        onDone: (data) => {
          sessionId.value = data.session_id
          if (data.test_cases?.length) {
            const rows = rowsFromTestCases(data.test_cases)
            panelDocument.value.tableRows = rows
            panelDocument.value.markdown = buildMarkdownFromRows(rows)
            panelDocument.value.mindmap = buildMindmapFromRows(rows)
            panelDocument.value.sync.revision += 1
            panelDocument.value.sync.lastEditedBy = 'system'
            panelDocument.value.sync.lastEditedAt = Date.now()
            canRestoreRaw.value = true
            outputTab.value = defaultRender.value
          }
          const msg = mockMessages.value[assistIdx]
          if (msg) {
            msg.content = '执行完成，结果请查看输出区'
            msg.streaming = false
            msg.streamContent = ''
            msg.currentStep = {
              stepId: 'done',
              label: '已完成',
              status: 'succeeded'
            }
            if (Array.isArray(msg.planSteps)) {
              const respondStep = msg.planSteps.find((s) => s.stepId === 'respond')
              if (respondStep) respondStep.status = 'succeeded'
            }
          }
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
          const messageItem = mockMessages.value[assistIdx]
          if (messageItem) {
            messageItem.content = `生成失败：${full}`
            messageItem.streaming = false
            messageItem.currentStep = {
              stepId: 'failed',
              label: '执行失败',
              status: 'failed'
            }
          }
        }
      },
      { signal: abortController.signal }
    )
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') {
      const last = mockMessages.value[mockMessages.value.length - 1]
      if (last?.role === 'assistant' && last.streaming) {
        last.content = '已停止生成'
        last.streaming = false
        if (last.currentStep?.status === 'running') {
          last.currentStep = {
            ...last.currentStep,
            status: 'failed'
          }
        }
      }
      message.info('已停止')
    }
  } finally {
    sending.value = false
    activeStreamAbort.value = null
  }
}

function handleStop() {
  if (!sending.value) return
  activeStreamAbort.value?.abort()
}

async function handleSave() {
  if (!sessionId.value) {
    message.warning('当前还没有可保存的会话')
    return
  }
  try {
    const res = await patchAgentSessionLatestEditedOutput(sessionId.value, {
      edited_payload: panelDocument.value,
      edited_revision: panelDocument.value.sync.revision
    })
    const rev = res.data?.edited_revision
    if (typeof rev === 'number' && Number.isFinite(rev)) {
      panelDocument.value.sync.revision = rev
      panelDocument.value.sync.lastEditedBy = outputTab.value
      panelDocument.value.sync.lastEditedAt = Date.now()
    }
    message.success('已保存，后续生成将基于当前编辑版')
  } catch {
    /* request 拦截器已提示 */
  }
}

async function handleExportExcel() {
  if (!sessionId.value) {
    message.warning('当前还没有可导出的会话')
    return
  }
  try {
    const { blob, fileName } = await getAgentSessionExportExcel(sessionId.value, 'edited')
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName || `testcases_${sessionId.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch (e) {
    message.error(e instanceof Error ? e.message : '导出失败')
  }
}

function resetSessionForSkillSwitch() {
  sessionId.value = null
  canRestoreRaw.value = false
  mockMessages.value = []
  panelDocument.value = {
    tableRows: [],
    markdown: '# 测试用例报告\n\n暂无数据。',
    mindmap: [],
    sync: {
      revision: 0,
      lastEditedBy: 'system',
      lastEditedAt: Date.now()
    }
  }
}

function handleNewSession() {
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

function dispatchActiveSessionChanged() {
  const detail: AgentActiveSessionDetail = { sessionId: sessionId.value }
  window.dispatchEvent(new CustomEvent(AGENT_ACTIVE_SESSION_CHANGED, { detail }))
}

watch(sessionId, () => {
  dispatchActiveSessionChanged()
})

function onSidebarNewSessionEvent() {
  handleNewSession()
}

function onSidebarOpenSessionEvent(e: Event) {
  const d = (e as CustomEvent<AgentSidebarOpenSessionDetail>).detail
  if (!d?.sessionId) return
  void onSelectHistorySession({
    sessionId: d.sessionId,
    skillId: (d.skillId || 'test_case_gen').trim() || 'test_case_gen',
  })
}

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

function assistantBriefFromApiMessage(_content: Record<string, unknown>): string {
  return '执行完成，结果请查看输出区'
}

const STEP_ORDER: Record<string, number> = {
  plan: 0,
  call_skill: 1,
  parse_output: 2,
  persist: 3,
  respond: 4
}

function sortPlanSteps(
  steps: AgentChatMessage['planSteps']
): NonNullable<AgentChatMessage['planSteps']> {
  return [...(steps || [])].sort((a, b) => {
    const ai = STEP_ORDER[a.stepId] ?? 99
    const bi = STEP_ORDER[b.stepId] ?? 99
    if (ai !== bi) return ai - bi
    return a.stepId.localeCompare(b.stepId)
  })
}

function buildPlanStepsFromContentJson(
  content: Record<string, unknown>
): NonNullable<AgentChatMessage['planSteps']> {
  const raw = content.plan_steps
  if (!Array.isArray(raw)) return []
  return sortPlanSteps(
    raw
    .map((x) => (x && typeof x === 'object' ? (x as Record<string, unknown>) : null))
    .filter((x): x is Record<string, unknown> => !!x)
    .map((x) => ({
      stepId: String(x.step_id || '').trim(),
      label: String(x.label || x.step_id || '').trim(),
      status: String(x.status || 'pending') as 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped'
    }))
    .filter((x) => !!x.stepId)
  )
}

function buildPlanStepsFromExecution(
  execution: AgentHistoryMessageOut['execution']
): NonNullable<AgentChatMessage['planSteps']> {
  if (!execution?.traces?.length) return []
  return sortPlanSteps(
    execution.traces.map((t) => ({
      stepId: t.step_id,
      label: t.step_id,
      status: t.status
    }))
  )
}

function buildCurrentStepFromExecution(
  execution: AgentHistoryMessageOut['execution']
): AgentChatMessage['currentStep'] {
  if (!execution?.traces?.length) return null
  const failed = execution.traces.find((t) => t.status === 'failed')
  if (failed) {
    return { stepId: failed.step_id, label: failed.step_id, status: 'failed' }
  }
  const running = execution.traces.find((t) => t.status === 'running')
  if (running) {
    return { stepId: running.step_id, label: running.step_id, status: 'running' }
  }
  const last = execution.traces[execution.traces.length - 1]
  return { stepId: last.step_id, label: last.step_id, status: last.status }
}

function tryHydrateDocumentFromHistory(messages: AgentHistoryMessageOut[]): void {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i]
    if (m.role !== 'assistant') continue
    const edited = m.content_json?.edited_payload
    const rawPayload = m.content_json?.raw_payload
    canRestoreRaw.value = !!(rawPayload && typeof rawPayload === 'object')
    if (edited && typeof edited === 'object') {
      panelDocument.value = normalizeDocumentPayload(edited)
      outputTab.value = defaultRender.value
      return
    }
    if (rawPayload && typeof rawPayload === 'object') {
      panelDocument.value = normalizeDocumentPayload(rawPayload)
      outputTab.value = defaultRender.value
      return
    }
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
        const rows = rowsFromTestCases(parsed as TestCaseItem[])
        panelDocument.value.tableRows = rows
        panelDocument.value.markdown = buildMarkdownFromRows(rows)
        panelDocument.value.mindmap = buildMindmapFromRows(rows)
        panelDocument.value.sync.revision = 0
        panelDocument.value.sync.lastEditedBy = 'system'
        panelDocument.value.sync.lastEditedAt = Date.now()
        outputTab.value = defaultRender.value
        return
      }
    } catch {
      /* 非 JSON 或结构不符 */
    }
  }
  panelDocument.value.tableRows = []
  panelDocument.value.markdown = '# 测试用例报告\n\n暂无数据。'
  panelDocument.value.mindmap = []
  canRestoreRaw.value = false
  outputTab.value = defaultRender.value
}

async function handleRestoreRaw() {
  if (!sessionId.value) {
    message.warning('当前还没有可恢复的会话')
    return
  }
  try {
    const res = await patchAgentSessionRestoreLatestRawOutput(sessionId.value)
    if (res.data?.edited_payload && typeof res.data.edited_payload === 'object') {
      panelDocument.value = normalizeDocumentPayload(res.data.edited_payload)
    }
    if (typeof res.data?.edited_revision === 'number') {
      panelDocument.value.sync.revision = res.data.edited_revision
      panelDocument.value.sync.lastEditedBy = 'system'
      panelDocument.value.sync.lastEditedAt = Date.now()
    }
    outputTab.value = defaultRender.value
    message.success('已恢复为原始版')
  } catch {
    /* request 拦截器已提示 */
  }
}

async function onSelectHistorySession(payload: { sessionId: string; skillId: string }) {
  const { sessionId: sid, skillId } = payload
  setLayoutMode('split')
  historySessionLoading.value = true
  try {
    const res = await getAgentSessionMessages(sid)
    const data = res.data
    if (!data) {
      message.warning('未拉取到会话数据')
      return
    }
    sessionId.value = data.session_id
    applySkillId((skillId || data.skill_id || 'test_case_gen').trim() || 'test_case_gen')
    mockMessages.value = data.messages.map((m) => {
      const contentJson = m.content_json as Record<string, unknown>
      const planStepsFromContent = buildPlanStepsFromContentJson(contentJson)
      const planSteps =
        m.role === 'assistant'
          ? planStepsFromContent.length
            ? planStepsFromContent
            : buildPlanStepsFromExecution(m.execution)
          : []
      const currentStep =
        m.role === 'assistant'
          ? planSteps.length
            ? planSteps[planSteps.length - 1]
            : buildCurrentStepFromExecution(m.execution)
          : null
      return {
        id: String(m.id),
        role: m.role,
        content:
          m.role === 'user'
            ? userTextFromApiMessage(contentJson)
            : assistantBriefFromApiMessage(contentJson),
        streamContent: '',
        streaming: false,
        currentStep,
        planSteps
      }
    })
    tryHydrateDocumentFromHistory(data.messages)
  } catch {
    /* request 拦截器已提示 */
  } finally {
    historySessionLoading.value = false
  }
}

/** 双栏时对话在左、输出在右；分隔条可拖（左侧对话区定宽，右侧输出区占满剩余） */
const AGENT_CHAT_WIDTH_KEY = 'agent_chat_panel_width'
const AGENT_LAYOUT_MODE_KEY = 'agent_layout_mode'
const CHAT_PANEL_MIN = 280
const OUTPUT_PANEL_MIN = 260
const RESIZER_WIDTH = 6
const DEFAULT_CHAT_WIDTH = 400
type AgentLayoutMode = 'split' | 'output-only' | 'chat-only'

const agentBodyRef = ref<HTMLElement | null>(null)
const chatPanelWidthPx = ref(DEFAULT_CHAT_WIDTH)
const resizeDragging = ref(false)
const layoutMode = ref<AgentLayoutMode>('split')
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

function readStoredLayoutMode(): void {
  try {
    const raw = localStorage.getItem(AGENT_LAYOUT_MODE_KEY)
    if (raw === 'split' || raw === 'output-only' || raw === 'chat-only') {
      layoutMode.value = raw
    }
  } catch {
    /* ignore */
  }
}

function saveLayoutMode(mode: AgentLayoutMode): void {
  try {
    localStorage.setItem(AGENT_LAYOUT_MODE_KEY, mode)
  } catch {
    /* ignore */
  }
}

function setLayoutMode(mode: AgentLayoutMode): void {
  layoutMode.value = mode
  saveLayoutMode(mode)
  if (mode === 'split') {
    requestAnimationFrame(() => applyChatWidthToBody())
  }
}

function onResizePointerMove(clientX: number) {
  if (layoutMode.value !== 'split') return
  if (!resizeDragging.value || !agentBodyRef.value) return
  const bodyW = agentBodyRef.value.getBoundingClientRect().width
  const delta = clientX - resizeStartX
  /* 对话在左：向右拖 = 分隔条右移 = 对话区变宽；向左拖 = 变窄 */
  chatPanelWidthPx.value = clampChatWidth(resizeStartW + delta, bodyW)
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

function onResizePointerMoveEvent(e: PointerEvent) {
  onResizePointerMove(e.clientX)
}

function onResizePointerUpEvent() {
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
  if (layoutMode.value !== 'split') return
  e.preventDefault()
  resizeDragging.value = true
  resizeStartX = e.clientX
  resizeStartW = chatPanelWidthPx.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizePointerStart(e: PointerEvent) {
  if (layoutMode.value !== 'split') return
  // 统一 mouse/touch/pen，解决部分 Windows 设备不触发 mousemove 的问题
  e.preventDefault()
  resizeDragging.value = true
  resizeStartX = e.clientX
  resizeStartW = chatPanelWidthPx.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeTouchStart(e: TouchEvent) {
  if (layoutMode.value !== 'split') return
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
  if (layoutMode.value !== 'split') return
  if (!agentBodyRef.value) return
  const bodyW = agentBodyRef.value.getBoundingClientRect().width
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    chatPanelWidthPx.value = clampChatWidth(chatPanelWidthPx.value - 16, bodyW)
    try {
      localStorage.setItem(AGENT_CHAT_WIDTH_KEY, String(chatPanelWidthPx.value))
    } catch {
      /* ignore */
    }
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    chatPanelWidthPx.value = clampChatWidth(chatPanelWidthPx.value + 16, bodyW)
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
  readStoredLayoutMode()
  readStoredChatWidth()
  requestAnimationFrame(() => applyChatWidthToBody())
  dispatchActiveSessionChanged()
  window.addEventListener(AGENT_SIDEBAR_NEW_SESSION, onSidebarNewSessionEvent)
  window.addEventListener(AGENT_SIDEBAR_OPEN_SESSION, onSidebarOpenSessionEvent as EventListener)
  window.addEventListener('mousemove', onResizeMouseMove)
  window.addEventListener('mouseup', onResizeMouseUp)
  window.addEventListener('pointermove', onResizePointerMoveEvent)
  window.addEventListener('pointerup', onResizePointerUpEvent)
  window.addEventListener('pointercancel', onResizePointerUpEvent)
  window.addEventListener('touchmove', onResizeTouchMove, { passive: false })
  window.addEventListener('touchend', onResizeTouchEnd)
  window.addEventListener('touchcancel', onResizeTouchEnd)
  window.addEventListener('resize', applyChatWidthToBody)
})

onUnmounted(() => {
  window.dispatchEvent(
    new CustomEvent<AgentActiveSessionDetail>(AGENT_ACTIVE_SESSION_CHANGED, {
      detail: { sessionId: null },
    })
  )
  window.removeEventListener(AGENT_SIDEBAR_NEW_SESSION, onSidebarNewSessionEvent)
  window.removeEventListener(AGENT_SIDEBAR_OPEN_SESSION, onSidebarOpenSessionEvent as EventListener)
  window.removeEventListener('mousemove', onResizeMouseMove)
  window.removeEventListener('mouseup', onResizeMouseUp)
  window.removeEventListener('pointermove', onResizePointerMoveEvent)
  window.removeEventListener('pointerup', onResizePointerUpEvent)
  window.removeEventListener('pointercancel', onResizePointerUpEvent)
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
    <WorkbenchHeader :title="workbenchTitle" :layout-mode="layoutMode" @update:layout-mode="setLayoutMode" />
    <div
      ref="agentBodyRef"
      class="agent-body"
      :class="{
        'agent-body--resizing': resizeDragging,
        'agent-body--output-only': layoutMode === 'output-only',
        'agent-body--chat-only': layoutMode === 'chat-only'
      }"
    >
      <div
        v-show="layoutMode !== 'output-only'"
        class="agent-body__chat"
        :style="layoutMode === 'split' ? { width: `${chatPanelWidthPx}px` } : undefined"
      >
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
          :history-session-loading="historySessionLoading"
          @send="handleSend"
          @stop="handleStop"
          @skill-change="handleSkillChange"
          @show-output="setLayoutMode('split')"
          @apply-prompt="applyWelcomePrompt"
        />
      </div>
      <div
        v-show="layoutMode === 'split'"
        class="agent-body__resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label="拖动调节对话区与输出区宽度"
        tabindex="0"
        @pointerdown="onResizePointerStart"
        @mousedown="onResizeStart"
        @touchstart.prevent="onResizeTouchStart"
        @keydown="onResizeKeydown"
      />
      <div v-show="layoutMode !== 'chat-only'" class="agent-body__output">
        <OutputPanel
          v-model:document="panelDocument"
          v-model:output-tab="outputTab"
          :session-id="sessionId"
          :can-restore-raw="canRestoreRaw"
          :render-modes="renderModes"
          :table-columns="tableColumns"
          @save="handleSave"
          @export-excel="handleExportExcel"
          @restore-raw="handleRestoreRaw"
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
  height: 100vh;
  max-height: 100vh;
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

.agent-body--output-only .agent-body__output,
.agent-body--chat-only .agent-body__chat {
  flex: 1;
  width: 100%;
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
