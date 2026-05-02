/** 布局侧栏与测试助手页之间的 CustomEvent 名称（document/window） */
export const AGENT_SIDEBAR_NEW_SESSION = 'agent-sidebar-new-session'
export const AGENT_SIDEBAR_OPEN_SESSION = 'agent-sidebar-open-session'
export const AGENT_ACTIVE_SESSION_CHANGED = 'agent-active-session-changed'

export type AgentSidebarOpenSessionDetail = {
  sessionId: string
  skillId: string
}

export type AgentActiveSessionDetail = {
  sessionId: string | null
}
