import type {
  AgentChatAckData,
  AgentChatRequest,
  AgentStreamDonePayload,
  TextPart
} from '@/schemas/agent'
import type { TestCaseItem } from '@/schemas/testcase'
import api, { getAccessToken } from '@/utils/request'

/** 非流式：一次返回完整结果 */
export function postAgentChat(body: AgentChatRequest) {
  return api.post<AgentChatAckData>('/agent/chat', body)
}

type StreamHandlers = {
  onToken?: (text: string) => void
  onDone?: (data: AgentStreamDonePayload) => void
  onError?: (message: string, details?: unknown) => void
}

/**
 * SSE：`POST /api/agent/chat/stream`（见 docs/agent-sse-protocol.md）
 */
export async function postAgentChatStream(
  body: AgentChatRequest,
  handlers: StreamHandlers
): Promise<void> {
  const base = import.meta.env.VITE_API_BASE_URL || '/api'
  const url = `${String(base).replace(/\/$/, '')}/agent/chat/stream`
  const token = getAccessToken()
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  })

  if (!res.ok) {
    let msg = `请求失败 (${res.status})`
    try {
      const j = await res.json()
      if (j?.message) msg = j.message
    } catch {
      /* ignore */
    }
    handlers.onError?.(msg)
    throw new Error(msg)
  }

  const reader = res.body?.getReader()
  if (!reader) {
    handlers.onError?.('无法读取响应流')
    throw new Error('无法读取响应流')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  const parseFrame = (frame: string) => {
    let eventName = 'message'
    let dataLine: string | null = null
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLine = line.slice(5).trim()
      }
    }
    if (dataLine == null) return
    const payload = JSON.parse(dataLine) as Record<string, unknown>
    if (eventName === 'token' && typeof payload.text === 'string') {
      handlers.onToken?.(payload.text)
    } else if (eventName === 'done') {
      const d = payload as unknown as AgentStreamDonePayload
      const parts = (d.parts || []) as TextPart[]
      const test_cases = (d.test_cases || []) as TestCaseItem[]
      handlers.onDone?.({
        session_id: String(d.session_id),
        skill_id: String(d.skill_id),
        parts,
        test_cases,
        used_template: d.used_template
      })
    } else if (eventName === 'error') {
      handlers.onError?.(String(payload.message || '流式生成失败'), payload.details)
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 2)
      if (frame) {
        try {
          parseFrame(frame)
        } catch (e) {
          handlers.onError?.('解析 SSE 数据失败', e)
        }
      }
    }
  }
}
