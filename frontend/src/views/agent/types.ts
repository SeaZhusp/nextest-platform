/** 智能体对话消息（与页面 / 接口演进对齐） */
export interface AgentStepState {
  stepId: string
  label: string
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped'
}

export interface AgentChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  streamContent?: string
  streaming?: boolean
  currentStep?: AgentStepState | null
  planSteps?: AgentStepState[]
}

/** 输出区 Tab（当前面板实现 table / markdown；mindmap 预留与技能 render_modes 对齐） */
export type AgentOutputTabKey = 'table' | 'markdown' | 'mindmap'

export interface TestCaseRow {
  key: string
  case_no: string
  module: string
  title: string
  preconditions: string
  steps: string
  expected: string
  priority: string
}

export interface MindmapNode {
  key: string
  title: string
  children?: MindmapNode[]
}

export interface DocumentSync {
  revision: number
  lastEditedBy: AgentOutputTabKey | 'system'
  lastEditedAt: number
}

export interface DocumentModel {
  /** 与后端 raw_payload / edited_payload 字段名 `table` 对齐 */
  table: TestCaseRow[]
  markdown: string
  mindmap: MindmapNode[]
  sync: DocumentSync
}
