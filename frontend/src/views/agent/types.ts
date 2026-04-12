/** 智能体对话消息（与页面 / 接口演进对齐） */
export interface AgentChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  done?: boolean
}

/** 输出区 Tab（与 AgentOutputPanel 一致） */
export type AgentOutputTabKey = 'table' | 'editor' | 'preview'
