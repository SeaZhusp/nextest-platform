import type {
  AgentChatAckData,
  AgentChatRequest,
  AgentExecutionSummaryOut,
  AgentSessionLatestEditedOutputData,
  AgentSessionLatestEditedOutputRequest,
  AgentSessionListData,
  AgentSessionMessagesData,
  AgentSessionRenameRequest,
  AgentSessionSummaryOut,
  AgentStreamDonePayload,
  TextPart
} from '@/schemas/agent'
import type { TestCaseItem } from '@/schemas/testcase'
import api, { getAccessToken } from '@/utils/request'

/** 非流式：一次返回完整结果 */
export function postAgentChat(body: AgentChatRequest) {
  return api.post<AgentChatAckData>('/agent/chat', body)
}

/** 历史会话分页列表 */
export function getAgentSessions(params: { page?: number; size?: number }) {
  return api.get<AgentSessionListData>('/agent/sessions', { params })
}

/** 某会话消息（含 title / skill_id） */
export function getAgentSessionMessages(sessionId: string) {
  return api.get<AgentSessionMessagesData>(`/agent/sessions/${sessionId}/messages`)
}

/** 某会话 execution 汇总（看板聚合） */
export function getAgentExecutionSummary(sessionId: string) {
  return api.get<AgentExecutionSummaryOut>(`/agent/sessions/${sessionId}/execution-summary`)
}

/** 重命名会话 */
export function patchAgentSessionTitle(sessionId: string, body: AgentSessionRenameRequest) {
  return api.patch<AgentSessionSummaryOut>(`/agent/sessions/${sessionId}`, body)
}

/** 保存会话最后一条 assistant 编辑版结果 */
export function patchAgentSessionLatestEditedOutput(
  sessionId: string,
  body: AgentSessionLatestEditedOutputRequest
) {
  return api.patch<AgentSessionLatestEditedOutputData>(
    `/agent/sessions/${sessionId}/messages/latest-edited-output`,
    body
  )
}

/** 一键恢复会话最后一条消息为 raw 版本 */
export function patchAgentSessionRestoreLatestRawOutput(sessionId: string) {
  return api.patch<AgentSessionLatestEditedOutputData>(
    `/agent/sessions/${sessionId}/messages/latest-edited-output/restore-raw`
  )
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
