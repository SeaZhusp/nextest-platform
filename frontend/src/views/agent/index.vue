<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { postAgentChatStream } from '@/api/agent'
import { listUserLlmProfiles } from '@/api/userLlmProfiles'
import type { AgentStreamDonePayload } from '@/schemas/agent'
import { listSkills } from '@/api/skills'
import { buildTextParts, validatePhase1UserInput } from '@/schemas/agent'
import type { TestCaseItem } from '@/schemas/testcase'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'
import AgentOutputPanel from './components/AgentOutputPanel.vue'
import AgentChatPanel from './components/AgentChatPanel.vue'
import type { AgentChatMessage, AgentOutputTabKey } from './types'

const route = useRoute()

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
        skill_id: 'test_case_gen',
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
        onError: (msg) => {
          message.error(msg)
          mockMessages.value[assistIdx].content = `生成失败：${msg}`
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

async function handleNewSession() {
  sessionId.value = null
  mockMessages.value = []
  let skillHint = ''
  try {
    const res = await listSkills()
    const names = (res.data ?? []).map((s) => s.skill_id).join(', ')
    skillHint = names ? ` 已注册技能：${names}。` : ' 当前无已注册技能。'
  } catch {
    skillHint = ''
  }
  message.info(`已清空会话（演示）。${skillHint}后续可接后端新会话接口。`)
}

function handleHistory() {
  message.info('历史会话（演示），后续可接列表接口')
}
</script>

<template>
  <div class="agent-page">
    <div class="agent-body">
      <AgentOutputPanel
        v-model:editor-json="editorJsonText"
        v-model:output-tab="outputTab"
        :session-id="sessionId"
        :table-columns="tableColumns"
        :rows="mockTestCases"
        :markdown-report="markdownReport"
        @save="handleSave"
      />
      <AgentChatPanel
        v-model:input-text="inputText"
        v-model:selected-profile-id="selectedProfileId"
        v-model:temperature="temperature"
        :messages="mockMessages"
        :sending="sending"
        :profiles="llmProfiles"
        :profiles-loading="profilesLoading"
        @send="handleSend"
        @new-session="handleNewSession"
        @history="handleHistory"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.agent-page {
  height: 100%;
  min-height: calc(100vh - 128px);
  display: flex;
  flex-direction: column;
}

.agent-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  background: #fff;
}
</style>
