<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import {
  EditOutlined,
  HistoryOutlined,
  MessageOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getAgentSessions, patchAgentSessionTitle } from '@/api/agent'
import type { AgentSessionSummaryOut } from '@/schemas/agent'

const open = defineModel<boolean>('open', { default: false })

const emit = defineEmits<{
  select: [payload: { sessionId: string; skillId: string }]
}>()

const loading = ref(false)
const loadingMore = ref(false)
const items = ref<AgentSessionSummaryOut[]>([])
const total = ref(0)
const pageSize = 10

const listRef = ref<HTMLElement | null>(null)

const renameVisible = ref(false)
const renameSubmitting = ref(false)
const renameInput = ref('')
const renameTarget = ref<AgentSessionSummaryOut | null>(null)

const hasMore = computed(() => total.value > 0 && items.value.length < total.value)

function formatRelativeTime(iso: string): string {
  if (!iso?.trim()) return ''
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return ''
  const diff = Date.now() - t
  if (diff < 0) return '刚刚'
  const sec = Math.floor(diff / 1000)
  const min = Math.floor(sec / 60)
  const hr = Math.floor(min / 60)
  const day = Math.floor(hr / 24)
  if (day >= 30) return `${Math.floor(day / 30)}个月前`
  if (day >= 1) return `${day}天前`
  if (hr >= 1) return `${hr}小时前`
  if (min >= 1) return `${min}分钟前`
  return '刚刚'
}

/** 首屏或刷新：清空后拉第 1 页 */
async function fetchList(append: boolean) {
  if (!open.value) return
  if (append) {
    if (items.value.length === 0 || !hasMore.value || loadingMore.value || loading.value) return
    loadingMore.value = true
  } else {
    if (loading.value) return
    loading.value = true
    items.value = []
    total.value = 0
  }

  const nextPage = append ? Math.ceil(items.value.length / pageSize) + 1 : 1

  try {
    const res = await getAgentSessions({ page: nextPage, size: pageSize })
    const chunk = res.data?.items ?? []
    const t = res.data?.total ?? 0
    total.value = t
    if (append && !chunk.length) {
      total.value = items.value.length
      return
    }
    if (append) {
      items.value = [...items.value, ...chunk]
    } else {
      items.value = chunk
    }
  } catch {
    if (!append) {
      items.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
    loadingMore.value = false
    await nextTick()
    void fillUntilScrollableOrDone()
  }
}

/** 列表高度不够出现滚动条时，自动继续请求直到有滚动或已全部加载 */
async function fillUntilScrollableOrDone() {
  const root = listRef.value
  if (!open.value || !root || loading.value || loadingMore.value) return
  let guard = 0
  while (
    guard < 40 &&
    open.value &&
    items.value.length < total.value &&
    root.scrollHeight <= root.clientHeight + 6
  ) {
    guard++
    await fetchList(true)
    await nextTick()
  }
}

function onListScroll() {
  const el = listRef.value
  if (!el || loading.value || loadingMore.value || !hasMore.value) return
  const threshold = 80
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold) {
    void fetchList(true)
  }
}

function refresh() {
  void fetchList(false)
}

watch(
  () => open.value,
  (v) => {
    if (v) void fetchList(false)
  }
)

function onSelect(record: AgentSessionSummaryOut) {
  emit('select', { sessionId: record.session_id, skillId: record.skill_id })
  open.value = false
}

function openRename(record: AgentSessionSummaryOut, e: MouseEvent) {
  e.stopPropagation()
  renameTarget.value = record
  renameInput.value = record.title || ''
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
    renameVisible.value = false
    renameTarget.value = null
    await fetchList(false)
  } catch {
    /* 拦截器已提示 */
  } finally {
    renameSubmitting.value = false
  }
}

function displayTitle(record: AgentSessionSummaryOut) {
  const t = (record.title || '').trim()
  return t || '（无标题）'
}
</script>

<template>
  <a-popover
    v-model:open="open"
    trigger="click"
    placement="bottomRight"
    :arrow="{ pointAtCenter: true }"
    overlay-class-name="session-history-popover"
  >
    <template #content>
      <div class="session-history">
        <div class="session-history__head">
          <div class="session-history__head-title">
            <HistoryOutlined class="session-history__head-icon" />
            <span>历史会话</span>
          </div>
          <a-button
            type="text"
            size="small"
            class="session-history__refresh"
            :loading="loading"
            title="刷新"
            @click="refresh"
          >
            <ReloadOutlined />
          </a-button>
        </div>

        <div class="session-history__list-pane">
          <a-spin :spinning="loading" wrapper-class-name="session-history__spin-wrap">
            <div v-if="!loading && !items.length" class="session-history__empty">
              暂无会话记录，发送一条消息后会出现在这里
            </div>
            <div
              v-else
              ref="listRef"
              class="session-history__list"
              :class="{ 'session-history__list--boot': loading && items.length === 0 }"
              @scroll.passive="onListScroll"
            >
              <ul class="session-history__list-inner" role="list">
                <li
                  v-for="row in items"
                  :key="row.session_id"
                  class="session-history__row"
                  role="button"
                  tabindex="0"
                  @click="onSelect(row)"
                  @keydown.enter.prevent="onSelect(row)"
                >
                  <div class="session-history__avatar" aria-hidden="true">
                    <MessageOutlined />
                  </div>
                  <div class="session-history__body">
                    <div class="session-history__title" :title="displayTitle(row)">
                      {{ displayTitle(row) }}
                    </div>
                    <div class="session-history__meta">
                      {{ formatRelativeTime(row.updated_at) }}
                    </div>
                  </div>
                  <a-button
                    type="text"
                    size="small"
                    class="session-history__rename"
                    title="重命名"
                    @click="openRename(row, $event)"
                  >
                    <EditOutlined />
                  </a-button>
                </li>
              </ul>
              <div v-if="loadingMore" class="session-history__loading-more">加载中…</div>
              <div v-else-if="hasMore" class="session-history__hint">下滑加载更多</div>
              <div v-else-if="items.length > 0" class="session-history__end">没有更多了</div>
            </div>
          </a-spin>
        </div>
      </div>
    </template>

    <slot />
  </a-popover>

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
</template>

<style scoped lang="scss">
.session-history {
  box-sizing: border-box;
  width: 100%;
  overflow-x: hidden;
}

.session-history__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.session-history__head-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-weight: 600;
  font-size: 14px;
  color: #262626;

  > span:last-child {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.session-history__head-icon {
  font-size: 16px;
  color: #1677ff;
}

.session-history__refresh {
  flex-shrink: 0;
  color: #595959;
}

.session-history__list-pane {
  min-width: 0;
  max-width: 100%;
}

.session-history__list {
  max-height: 320px;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.session-history__list--boot {
  min-height: 200px;
}

.session-history__list-inner {
  list-style: none;
  margin: 0;
  padding: 0;
}

.session-history__row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  max-width: 100%;
  padding: 10px 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: #f5f5f5;

    .session-history__rename {
      opacity: 1;
      pointer-events: auto;
    }
  }
}

.session-history__avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  font-size: 16px;
}

.session-history__body {
  flex: 1;
  min-width: 0;
}

.session-history__title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-history__meta {
  margin-top: 4px;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-history__rename {
  flex-shrink: 0;
  align-self: center;
  opacity: 0;
  pointer-events: none;
  color: #595959;
  transition: opacity 0.12s ease;

  &:hover {
    color: #1677ff;
  }
}

.session-history__empty {
  padding: 20px 8px;
  text-align: center;
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.5;
}

.session-history__loading-more,
.session-history__hint,
.session-history__end {
  padding: 10px 4px 6px;
  text-align: center;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
}

.session-history__end {
  color: #bfbfbf;
}

.session-history__list-pane :deep(.session-history__spin-wrap.ant-spin-nested-loading),
.session-history__list-pane :deep(.session-history__spin-wrap .ant-spin-container) {
  max-width: 100%;
  overflow-x: hidden;
}
</style>

<style lang="scss">
.session-history__spin-wrap.ant-spin-nested-loading {
  width: 100%;
}

.session-history__spin-wrap.ant-spin-nested-loading > .ant-spin-container::after {
  border-radius: 8px;
}

/* 固定外层宽度：避免加载 / 空态 / 列表切换时 Popover 随内容宽窄抖动 */
.session-history-popover .ant-popover-inner {
  box-sizing: border-box;
  width: min(320px, calc(100vw - 24px));
  max-width: min(320px, calc(100vw - 24px));
  padding: 12px 14px;
  border-radius: 10px;
  overflow-x: hidden;
  box-shadow:
    0 6px 16px 0 rgba(0, 0, 0, 0.08),
    0 3px 6px -4px rgba(0, 0, 0, 0.12),
    0 9px 28px 8px rgba(0, 0, 0, 0.05);
}

.session-history-popover .ant-popover-inner-content {
  box-sizing: border-box;
  width: 100%;
  overflow-x: hidden;
}
</style>
