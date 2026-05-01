/** 智能体对话消息（与页面 / 接口演进对齐） */
export interface AgentChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  done?: boolean
}

/** 输出区 Tab（与 OutputPanel 一致） */
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
  tableRows: TestCaseRow[]
  markdown: string
  mindmap: MindmapNode[]
  sync: DocumentSync
}
