<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MessageOutlined, MoreOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { deleteAgentSession, getAgentSessions, patchAgentSessionTitle } from '@/api/agent'
import { formatRelativeTime } from '@/utils/time'
import type { AgentSessionSummaryOut } from '@/schemas/agent'
import {
  AGENT_ACTIVE_SESSION_CHANGED,
  AGENT_SIDEBAR_NEW_SESSION,
  AGENT_SIDEBAR_OPEN_SESSION,
  type AgentActiveSessionDetail,
} from '@/constants/agentSidebarBridge'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const loadingMore = ref(false)
const sessionItems = ref<AgentSessionSummaryOut[]>([])
const sessionTotal = ref(0)
const pageSize = 10
const listRef = ref<HTMLElement | null>(null)
const activeSessionId = ref<string | null>(null)
const listScrollbarVisible = ref(false)
const listScrollbarHideTimer = ref<ReturnType<typeof setTimeout> | null>(null)

function bumpListScrollbarVisible() {
  listScrollbarVisible.value = true
  if (listScrollbarHideTimer.value) {
    clearTimeout(listScrollbarHideTimer.value)
  }
  listScrollbarHideTimer.value = setTimeout(() => {
    listScrollbarVisible.value = false
    listScrollbarHideTimer.value = null
  }, 900)
}

const hasMore = computed(
  () => sessionTotal.value > 0 && sessionItems.value.length < sessionTotal.value
)

function displayTitle(record: AgentSessionSummaryOut) {
  const t = (record.title || '').trim()
  return t || '（无标题）'
}

async function fetchSessionList(append: boolean) {
  if (append) {
    if (
      sessionItems.value.length === 0 ||
      !hasMore.value ||
      loadingMore.value ||
      loading.value
    ) {
      return
    }
    loadingMore.value = true
  } else {
    if (loading.value) return
    loading.value = true
    sessionItems.value = []
    sessionTotal.value = 0
  }

  const nextPage = append ? Math.ceil(sessionItems.value.length / pageSize) + 1 : 1

  try {
    const res = await getAgentSessions({ page: nextPage, size: pageSize })
    const chunk = res.data?.items ?? []
    const t = res.data?.total ?? 0
    sessionTotal.value = t
    if (append && !chunk.length) {
      sessionTotal.value = sessionItems.value.length
      return
    }
    if (append) {
      sessionItems.value = [...sessionItems.value, ...chunk]
    } else {
      sessionItems.value = chunk
    }
  } catch {
    if (!append) {
      sessionItems.value = []
      sessionTotal.value = 0
    }
  } finally {
    loading.value = false
    loadingMore.value = false
    await nextTick()
    void fillUntilScrollableOrDone()
  }
}

async function fillUntilScrollableOrDone() {
  const root = listRef.value
  if (!root || loading.value || loadingMore.value) return
  let guard = 0
  while (
    guard < 40 &&
    sessionItems.value.length < sessionTotal.value &&
    root.scrollHeight <= root.clientHeight + 6
  ) {
    guard++
    await fetchSessionList(true)
    await nextTick()
  }
}

function onSessionListScroll() {
  bumpListScrollbarVisible()
  const el = listRef.value
  if (!el || loading.value || loadingMore.value || !hasMore.value) return
  const threshold = 80
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold) {
    void fetchSessionList(true)
  }
}

function onActiveSessionChanged(e: Event) {
  const d = (e as CustomEvent<AgentActiveSessionDetail>).detail
  activeSessionId.value = d?.sessionId ?? null
}

async function afterNavigateDispatch(fn: () => void) {
  await nextTick()
  requestAnimationFrame(() => {
    fn()
  })
}

async function openSession(record: AgentSessionSummaryOut) {
  if (route.path !== '/agent') {
    await router.push('/agent')
  }
  const skillId = (record.skill_id || 'test_case_gen').trim() || 'test_case_gen'
  await afterNavigateDispatch(() => {
    window.dispatchEvent(
      new CustomEvent(AGENT_SIDEBAR_OPEN_SESSION, {
        detail: { sessionId: record.session_id, skillId },
      })
    )
  })
}

const renameVisible = ref(false)
const renameSubmitting = ref(false)
const renameInput = ref('')
const renameTarget = ref<AgentSessionSummaryOut | null>(null)
const deletingId = ref<string | null>(null)

function openRenameModal(record: AgentSessionSummaryOut) {
  renameTarget.value = record
  renameInput.value = (record.title || '').trim()
  renameVisible.value = true
}

async function handleRenameOk() {
  const t = renameInput.value.trim()
  if (!t) {
    message.warning('请输入标题')
    return
  }
  const row = renameTarget.value
  if (!row) return
  renameSubmitting.value = true
  try {
    await patchAgentSessionTitle(row.session_id, { title: t })
    message.success('已保存')
    const item = sessionItems.value.find((x) => x.session_id === row.session_id)
    if (item) item.title = t
    renameVisible.value = false
    renameTarget.value = null
  } catch {
    /* 拦截器已提示 */
  } finally {
    renameSubmitting.value = false
  }
}

async function handleDeleteSession(record: AgentSessionSummaryOut) {
  if (deletingId.value) return
  deletingId.value = record.session_id
  try {
    await deleteAgentSession(record.session_id)
    message.success('已删除会话')
    sessionItems.value = sessionItems.value.filter((x) => x.session_id !== record.session_id)
    sessionTotal.value = Math.max(0, sessionTotal.value - 1)
    if (activeSessionId.value === record.session_id) {
      activeSessionId.value = null
      window.dispatchEvent(new CustomEvent(AGENT_SIDEBAR_NEW_SESSION))
    }
    await nextTick()
    void fillUntilScrollableOrDone()
  } catch {
    /* 拦截器已提示 */
  } finally {
    deletingId.value = null
  }
}

function confirmDeleteSession(record: AgentSessionSummaryOut) {
  Modal.confirm({
    title: '确认删除该会话？',
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    onOk() {
      return handleDeleteSession(record)
    },
  })
}

function onSessionRowMenuClick(info: { key: string | number }, row: AgentSessionSummaryOut) {
  const key = String(info.key)
  if (key === 'rename') {
    openRenameModal(row)
    return
  }
  if (key === 'delete') {
    confirmDeleteSession(row)
  }
}

function loadList() {
  void fetchSessionList(false)
}

watch(
  () => route.path,
  (p) => {
    if (p === '/agent' || p.startsWith('/agent')) {
      loadList()
    }
  }
)

onMounted(() => {
  window.addEventListener(AGENT_ACTIVE_SESSION_CHANGED, onActiveSessionChanged as EventListener)
  loadList()
})

onUnmounted(() => {
  if (listScrollbarHideTimer.value) {
    clearTimeout(listScrollbarHideTimer.value)
    listScrollbarHideTimer.value = null
  }
  window.removeEventListener(AGENT_ACTIVE_SESSION_CHANGED, onActiveSessionChanged as EventListener)
})
</script>

<template>
  <div class="session-history">
    <div class="session-history__toolbar">
      <span class="session-history__toolbar-title">历史对话</span>
      <a-button
        type="text"
        size="small"
        class="session-history__refresh"
        :loading="loading && sessionItems.length === 0"
        title="刷新"
        @click="fetchSessionList(false)"
      >
        刷新
      </a-button>
    </div>

    <div class="session-history__scroll">
      <div v-if="loading && sessionItems.length === 0" class="session-history__loading">
        <a-spin />
      </div>
      <div v-else-if="!sessionItems.length" class="session-history__empty">
        暂无会话，新建会话开始对话
      </div>
      <div
        v-else
        ref="listRef"
        class="session-history__list"
        :class="{ 'session-history__list--thumb': listScrollbarVisible }"
        @scroll.passive="onSessionListScroll"
      >
        <div
          v-for="row in sessionItems"
          :key="row.session_id"
          class="session-history__row"
          :class="{ 'session-history__row--active': activeSessionId === row.session_id }"
        >
          <button
            type="button"
            class="session-history__row-main"
            :title="displayTitle(row)"
            @click="openSession(row)"
          >
            <MessageOutlined class="session-history__row-icon" aria-hidden="true" />
            <div class="session-history__row-text">
              <span class="session-history__row-title">{{ displayTitle(row) }}</span>
              <span class="session-history__row-time">{{ formatRelativeTime(row.updated_at) }}</span>
            </div>
          </button>
          <div class="session-history__row-actions" @click.stop>
            <a-dropdown trigger="click" placement="bottomRight">
              <a-button
                type="text"
                size="small"
                class="session-history__row-more"
                title="更多"
                aria-label="更多操作"
                :loading="deletingId === row.session_id"
                @click.stop
              >
                <MoreOutlined />
              </a-button>
              <template #overlay>
                <a-menu @click="onSessionRowMenuClick($event, row)">
                  <a-menu-item key="rename">重命名</a-menu-item>
                  <a-menu-item key="delete" danger>删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
        <div v-if="loadingMore" class="session-history__footer">加载中…</div>
        <div v-else-if="hasMore" class="session-history__footer session-history__footer--hint">
          下拉加载更多
        </div>
        <div v-else-if="sessionItems.length > 0" class="session-history__footer session-history__footer--end">
          没有更多了
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="renameVisible"
      title="重命名会话"
      :confirm-loading="renameSubmitting"
      ok-text="保存"
      destroy-on-close
      @ok="handleRenameOk"
    >
      <a-input v-model:value="renameInput" maxlength="200" show-count placeholder="会话标题" />
    </a-modal>
  </div>
</template>

<style lang="scss" scoped>
.session-history {
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  padding: 0 8px 8px;
  overflow: hidden;
}

.session-history__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  padding: 0 2px;
}

.session-history__toolbar-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.45);
}

.session-history__refresh {
  padding: 0 4px;
  height: 24px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.session-history__scroll {
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.session-history__loading {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 8px;
}

.session-history__empty {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
  font-size: 12px;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.35);
  text-align: center;
}

.session-history__list {
  flex: 1 1 0;
  min-height: 0;
  max-height: 100%;
  overflow-x: hidden;
  overflow-y: scroll;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;

  &--thumb {
    scrollbar-color: rgba(0, 0, 0, 0.14) transparent;
  }

  &::-webkit-scrollbar {
    width: 5px;
  }

  &::-webkit-scrollbar-button {
    display: none;
    width: 0;
    height: 0;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: transparent;
    border-radius: 100px;
  }

  &--thumb::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.12);
  }

  &--thumb::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.18);
  }
}

.session-history__row {
  display: flex;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  margin: 0 0 4px;
  padding: 6px 4px 6px 6px;
  border-radius: 6px;
  background: transparent;
  color: inherit;
  transition: background-color 0.15s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.04);

    .session-history__row-actions {
      opacity: 1;
    }
  }

  &--active {
    background: rgba(24, 144, 255, 0.08);
    color: #1890ff;

    .session-history__row-actions {
      opacity: 1;
    }
  }

  &--active:hover {
    background: rgba(24, 144, 255, 0.1);
  }
}

.session-history__row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 2px 2px;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  text-align: left;
  color: inherit;
  font: inherit;
}

.session-history__row-icon {
  flex-shrink: 0;
  margin-top: 3px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.35);
}

.session-history__row--active .session-history__row-icon {
  color: #1890ff;
}

.session-history__row-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-history__row-title {
  font-size: 13px;
  line-height: 1.25;
  color: rgba(0, 0, 0, 0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-history__row--active .session-history__row-title {
  color: #1890ff;
}

.session-history__row-time {
  font-size: 11px;
  line-height: 1.2;
  color: rgba(0, 0, 0, 0.38);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-history__row--active .session-history__row-time {
  color: rgba(24, 144, 255, 0.72);
}

.session-history__row-actions {
  flex-shrink: 0;
  align-self: center;
  display: flex;
  align-items: center;
  opacity: 1;
}

@media (hover: hover) and (pointer: fine) {
  .session-history__row-actions {
    opacity: 0;
  }

  .session-history__row:hover .session-history__row-actions,
  .session-history__row--active .session-history__row-actions {
    opacity: 1;
  }
}

.session-history__row-more {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.session-history__row--active .session-history__row-more {
  color: rgba(24, 144, 255, 0.85);
}

.session-history__footer {
  padding: 8px 4px 4px;
  font-size: 11px;
  text-align: center;
  color: rgba(0, 0, 0, 0.35);

  &--hint {
    color: rgba(0, 0, 0, 0.28);
  }

  &--end {
    color: rgba(0, 0, 0, 0.25);
  }
}
</style>
