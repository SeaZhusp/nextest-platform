/**
 * 智能体用户输入契约（对齐后端 app/schemas/agent.py，阶段一 2.2.1）。
 * 推荐使用 `parts`；`content` 为便捷字段（单段 text）。
 */
import type { TestCaseItem } from '@/schemas/testcase'

/** 与后端 MessagePart discriminator 对齐 */
export type MessagePartType =
  | 'text'
  | 'image_url'
  | 'image_base64'
  | 'audio_url'
  | 'file_ref'

export interface TextPart {
  type: 'text'
  text: string
}

export interface ImageUrlPart {
  type: 'image_url'
  url: string
  mime_type?: string | null
}

export interface ImageBase64Part {
  type: 'image_base64'
  data: string
  mime_type?: string | null
}

export interface AudioUrlPart {
  type: 'audio_url'
  url: string
}

export interface FileRefPart {
  type: 'file_ref'
  attachment_id: string
  storage_key?: string | null
}

export type MessagePart =
  | TextPart
  | ImageUrlPart
  | ImageBase64Part
  | AudioUrlPart
  | FileRefPart

/** POST /api/agent/chat 请求体 */
export interface AgentChatRequest {
  session_id?: string | null
  skill_id?: string | null
  parts?: MessagePart[] | null
  /** 与 parts 互斥：等价于单段 { type: 'text', text: content } */
  content?: string | null
  /** 用户自备大模型配置；不传则后端走模板等非 LLM 路径 */
  llm_profile_id?: number | null
  /** 0–2，默认由后端处理 */
  temperature?: number
}

export interface AgentChatAckData {
  session_id: string
  skill_id: string
  parts: TextPart[]
  /** 2.2.2 技能执行返回的结构化用例 */
  test_cases?: TestCaseItem[]
}

/** POST /api/agent/chat/stream 结束帧 data（2.2.3） */
export interface AgentStreamDonePayload {
  session_id: string
  skill_id: string
  parts: TextPart[]
  test_cases: TestCaseItem[]
  used_template?: boolean
}

/** GET /agent/sessions/{id}/messages */
export interface AgentHistoryMessageOut {
  id: number
  role: 'user' | 'assistant'
  content_json: Record<string, unknown>
  created_at: string
}

export interface AgentSessionMessagesData {
  session_id: string
  title: string
  skill_id: string
  messages: AgentHistoryMessageOut[]
}

export interface AgentSessionSummaryOut {
  session_id: string
  title: string
  skill_id: string
  updated_at: string
}

export interface AgentSessionListData {
  items: AgentSessionSummaryOut[]
  total: number
  page: number
  size: number
}

export interface AgentSessionRenameRequest {
  title: string
}

const MAX_TEXT = 5000

/** 将纯文本转为单段 parts（一期推荐写法） */
export function buildTextParts(text: string): TextPart[] {
  const t = text.trim()
  if (!t) return []
  return [{ type: 'text', text: t }]
}

/**
 * 客户端校验（一期）：仅 text；总长度 ≤ maxChars。
 * 后端仍会再次校验。
 */
export function validatePhase1UserInput(
  parts: MessagePart[],
  maxChars: number = MAX_TEXT
): { ok: true } | { ok: false; message: string } {
  if (!parts.length) {
    return { ok: false, message: '请输入内容' }
  }
  for (const p of parts) {
    if (p.type !== 'text') {
      return { ok: false, message: `当前仅支持文本输入，不支持片段类型：${p.type}` }
    }
  }
  const total = parts.reduce((n, p) => {
    if (p.type === 'text') return n + p.text.length
    return n
  }, 0)
  if (total > maxChars) {
    return { ok: false, message: `文本总长度不能超过 ${maxChars} 个字符（当前 ${total}）` }
  }
  return { ok: true }
}
