<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { getAgentExecutionSummary, getAgentSessionMessages, getAgentSessions } from '@/api/agent'
import type {
  AgentExecutionOut,
  AgentExecutionSummaryOut,
  AgentHistoryMessageOut,
  AgentSessionSummaryOut
} from '@/schemas/agent'

type SummaryState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; data: AgentExecutionSummaryOut }
  | { status: 'error'; error: string }

const page = ref(1)
const size = ref(10)
const total = ref(0)
const sessionsLoading = ref(false)
const sessions = ref<AgentSessionSummaryOut[]>([])

const q = ref('')

const summaryBySessionId = reactive<Record<string, SummaryState>>({})

const drawerOpen = ref(false)
const drawerLoading = ref(false)
const drawerSessionId = ref<string>('')
const drawerTitle = ref<string>('')
const drawerMessages = ref<AgentHistoryMessageOut[]>([])

const filteredSessions = computed(() => {
  const kw = q.value.trim().toLowerCase()
  if (!kw) return sessions.value
  return sessions.value.filter((s) => {
    const t = (s.title || '').toLowerCase()
    const sid = (s.skill_id || '').toLowerCase()
    const id = (s.session_id || '').toLowerCase()
    return t.includes(kw) || sid.includes(kw) || id.includes(kw)
  })
})

function fmtMs(ms: number): string {
  if (!Number.isFinite(ms)) return '-'
  if (ms < 1000) return `${ms}ms`
  const sec = ms / 1000
  if (sec < 60) return `${sec.toFixed(1)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m${s}s`
}

function statusColor(status?: string | null): string {
  if (status === 'succeeded') return 'green'
  if (status === 'failed') return 'red'
  if (status === 'partial') return 'orange'
  return 'default'
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    const res = await getAgentSessions({ page: page.value, size: size.value })
    const data = res.data
    sessions.value = data?.items ?? []
    total.value = data?.total ?? 0
    // reset summary state for current page items
    for (const s of sessions.value) {
      if (!summaryBySessionId[s.session_id]) {
        summaryBySessionId[s.session_id] = { status: 'idle' }
      }
    }
    void loadSummariesForVisiblePage()
  } catch {
    sessions.value = []
    total.value = 0
  } finally {
    sessionsLoading.value = false
  }
}

async function withConcurrencyLimit<T>(
  items: T[],
  limit: number,
  fn: (item: T) => Promise<void>
): Promise<void> {
  const queue = items.slice()
  const workers = new Array(Math.max(1, limit)).fill(null).map(async () => {
    while (queue.length) {
      const it = queue.shift()
      if (!it) return
      await fn(it)
    }
  })
  await Promise.all(workers)
}

async function loadSummariesForVisiblePage() {
  const ids = sessions.value.map((s) => s.session_id)
  await withConcurrencyLimit(ids, 6, async (sid) => {
    const st = summaryBySessionId[sid]
    if (st && (st.status === 'loading' || st.status === 'ready')) return
    summaryBySessionId[sid] = { status: 'loading' }
    try {
      const res = await getAgentExecutionSummary(sid)
      if (!res.data) {
        summaryBySessionId[sid] = { status: 'error', error: '无数据' }
        return
      }
      summaryBySessionId[sid] = { status: 'ready', data: res.data }
    } catch (e) {
      summaryBySessionId[sid] = { status: 'error', error: String((e as any)?.message || '加载失败') }
    }
  })
}

async function openDetail(s: AgentSessionSummaryOut) {
  drawerOpen.value = true
  drawerLoading.value = true
  drawerSessionId.value = s.session_id
  drawerTitle.value = s.title || s.session_id
  drawerMessages.value = []
  try {
    const res = await getAgentSessionMessages(s.session_id)
    drawerMessages.value = res.data?.messages ?? []
  } catch {
    message.error('加载会话消息失败')
  } finally {
    drawerLoading.value = false
  }
}

function assistantText(content: Record<string, unknown>): string {
  const t = typeof content.text === 'string' ? content.text : ''
  if (!t) return ''
  if (t.length > 240) return `${t.slice(0, 240)}…`
  return t
}

function onlyAssistantExecutions(msgs: AgentHistoryMessageOut[]): Array<{ msg: AgentHistoryMessageOut; ex: AgentExecutionOut }> {
  const out: Array<{ msg: AgentHistoryMessageOut; ex: AgentExecutionOut }> = []
  for (const m of msgs) {
    if (m.role !== 'assistant') continue
    const ex = m.execution ?? null
    if (!ex) continue
    out.push({ msg: m, ex })
  }
  return out
}

const drawerExecutions = computed(() => onlyAssistantExecutions(drawerMessages.value))

watch([page, size], () => {
  void loadSessions()
}, { immediate: true })

</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 12px">
    <a-card>
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap">
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
          <div style="font-weight: 600; font-size: 16px">执行看板</div>
          <a-input
            v-model:value="q"
            allow-clear
            placeholder="搜索标题 / skill_id / session_id（仅当前页过滤）"
            style="width: 360px; max-width: 100%"
          />
        </div>
        <div style="display:flex; gap: 8px; align-items:center;">
          <a-button @click="loadSessions" :loading="sessionsLoading">刷新</a-button>
        </div>
      </div>
    </a-card>

    <a-card>
      <a-table
        :data-source="filteredSessions"
        :loading="sessionsLoading"
        :pagination="false"
        row-key="session_id"
        size="middle"
      >
        <a-table-column title="标题" data-index="title" key="title" :width="260">
          <template #default="{ record }">
            <div style="display:flex; flex-direction: column; gap: 2px">
              <div style="font-weight: 600">{{ record.title || '-' }}</div>
              <div style="font-size: 12px; color: rgba(0,0,0,0.45)">{{ record.session_id }}</div>
            </div>
          </template>
        </a-table-column>

        <a-table-column title="技能" data-index="skill_id" key="skill_id" :width="140" />

        <a-table-column title="执行" key="exec" :width="220">
          <template #default="{ record }">
            <div v-if="summaryBySessionId[record.session_id]?.status === 'loading'">
              <a-skeleton :paragraph="false" :title="{ width: '120px' }" active />
            </div>
            <div v-else-if="summaryBySessionId[record.session_id]?.status === 'error'" style="color:#ff4d4f">
              {{ (summaryBySessionId[record.session_id] as any).error }}
            </div>
            <div v-else-if="summaryBySessionId[record.session_id]?.status === 'ready'">
              <template v-if="(summaryBySessionId[record.session_id] as any).data">
                <div style="display:flex; align-items:center; gap: 8px; flex-wrap: wrap">
                  <a-tag :color="statusColor((summaryBySessionId[record.session_id] as any).data.last_status)">
                    {{ (summaryBySessionId[record.session_id] as any).data.last_status || 'none' }}
                  </a-tag>
                  <span>
                    {{ (summaryBySessionId[record.session_id] as any).data.succeeded }}/{{ (summaryBySessionId[record.session_id] as any).data.total_executions }}
                  </span>
                  <span style="color: rgba(0,0,0,0.45)">
                    {{ fmtMs((summaryBySessionId[record.session_id] as any).data.total_duration_ms) }}
                  </span>
                </div>
              </template>
            </div>
            <div v-else style="color: rgba(0,0,0,0.45)">-</div>
          </template>
        </a-table-column>

        <a-table-column title="更新时间" data-index="updated_at" key="updated_at" :width="180" />

        <a-table-column title="操作" key="action" :width="160" fixed="right">
          <template #default="{ record }">
            <a-space>
              <a-button size="small" type="link" @click="openDetail(record)">查看明细</a-button>
            </a-space>
          </template>
        </a-table-column>
      </a-table>

      <div style="display:flex; justify-content:flex-end; margin-top: 12px">
        <a-pagination
          :current="page"
          :pageSize="size"
          :total="total"
          show-size-changer
          :pageSizeOptions="['10','20','50']"
          @change="(p: number) => (page = p)"
          @showSizeChange="(_p: number, s: number) => { page = 1; size = s }"
        />
      </div>
    </a-card>

    <a-drawer
      v-model:open="drawerOpen"
      :title="`会话明细：${drawerTitle}`"
      width="720"
      :destroyOnClose="true"
    >
      <a-spin :spinning="drawerLoading">
        <div style="display:flex; flex-direction: column; gap: 12px">
          <a-alert
            type="info"
            show-icon
            message="说明"
            description="仅展示 assistant 消息里包含的 execution 轨迹（后端已结构化解析）。"
          />

          <div v-if="drawerExecutions.length === 0" style="color: rgba(0,0,0,0.45)">
            暂无 execution 轨迹（可能是旧数据或尚未执行完成）。
          </div>

          <a-collapse v-else>
            <a-collapse-panel
              v-for="item in drawerExecutions"
              :key="String(item.msg.id)"
              :header="`#${item.msg.id} ${item.ex.status} - ${item.msg.created_at}`"
            >
              <div style="margin-bottom: 8px; color: rgba(0,0,0,0.6)">
                {{ assistantText(item.msg.content_json) }}
              </div>
              <a-table
                :data-source="item.ex.traces.map((t, idx) => ({ key: `${item.msg.id}-${idx}`, ...t }))"
                :pagination="false"
                size="small"
              >
                <a-table-column title="step_id" data-index="step_id" key="step_id" :width="220" />
                <a-table-column title="status" data-index="status" key="status" :width="120" />
                <a-table-column title="duration" key="duration_ms" :width="120">
                  <template #default="{ record }">{{ fmtMs(record.duration_ms) }}</template>
                </a-table-column>
                <a-table-column title="output" data-index="output_summary" key="output_summary" />
                <a-table-column title="error" data-index="error" key="error" />
              </a-table>
            </a-collapse-panel>
          </a-collapse>
        </div>
      </a-spin>
    </a-drawer>
  </div>
</template>

