<script setup lang="ts">
import { computed, ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  PlusOutlined,
  HistoryOutlined,
  RobotOutlined,
  SendOutlined,
  SaveOutlined,
  UnorderedListOutlined,
  CommentOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'

/** 假数据：会话消息 */
interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  /** 模拟流式已结束 */
  done?: boolean
}

const mockMessages = ref<ChatMessage[]>([
  {
    id: '1',
    role: 'user',
    content:
      '请根据以下需求生成登录模块的测试用例：支持手机号+验证码登录，验证码 5 分钟有效，错误 5 次锁定 30 分钟。'
  },
  {
    id: '2',
    role: 'assistant',
    content:
      '已根据你的描述生成 4 条用例（见左侧表格）。如需调整优先级或补充异常场景，可直接在表格中编辑，或继续告诉我。'
  },
  {
    id: '3',
    role: 'user',
    content: '把 TC-LOGIN-002 的优先级改为 P0，并在步骤里补充「断网重试」场景。'
  },
  {
    id: '4',
    role: 'assistant',
    content: '已更新：TC-LOGIN-002 优先级为 P0，步骤已增加断网重试说明。可在「编辑器」查看 JSON，在「预览」查看 Markdown 报告样式。'
  }
])

const inputText = ref('')
const outputTab = ref<'table' | 'editor' | 'preview'>('table')

/** 假数据：用例表格 */
const tableColumns = [
  { title: '编号', dataIndex: 'case_no', key: 'case_no', width: 110, ellipsis: true },
  { title: '模块', dataIndex: 'module', key: 'module', width: 90 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '前置条件', dataIndex: 'preconditions', key: 'preconditions', ellipsis: true },
  { title: '步骤', dataIndex: 'steps', key: 'steps', ellipsis: true },
  { title: '预期', dataIndex: 'expected', key: 'expected', ellipsis: true },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 }
]

const mockTestCases = [
  {
    key: '1',
    case_no: 'TC-LOGIN-001',
    module: '登录',
    title: '手机号+验证码登录成功',
    preconditions: '已注册手机号；验证码服务可用',
    steps: '1. 输入手机号\n2. 获取验证码\n3. 输入正确验证码\n4. 点击登录',
    expected: '进入首页，session 建立',
    priority: 'P1'
  },
  {
    key: '2',
    case_no: 'TC-LOGIN-002',
    module: '登录',
    title: '验证码过期',
    preconditions: '验证码已超过 5 分钟',
    steps: '1. 输入手机号并获取验证码\n2. 等待 5 分钟以上\n3. 输入该验证码\n4. [断网重试] 恢复网络后再次提交',
    expected: '提示验证码失效，不可登录',
    priority: 'P0'
  },
  {
    key: '3',
    case_no: 'TC-LOGIN-003',
    module: '登录',
    title: '连续输错验证码锁定',
    preconditions: '同一账号',
    steps: '连续输入错误验证码 5 次',
    expected: '账号锁定 30 分钟，提示剩余时间',
    priority: 'P1'
  },
  {
    key: '4',
    case_no: 'TC-LOGIN-004',
    module: '登录',
    title: '非法手机号格式',
    preconditions: '无',
    steps: '输入非 11 位或非法号段',
    expected: '前端校验拦截或后端返回格式错误',
    priority: 'P2'
  }
]

/** 与表格同步的 JSON 编辑器内容（假数据） */
const editorJsonText = ref(JSON.stringify(mockTestCases, null, 2))

/** Markdown 报告（假数据，用于预览 Tab） */
const markdownReport = ref(`# 登录模块测试用例说明（示例）

## 范围
- **需求**：手机号 + 验证码登录
- **生成时间**：演示数据

## 用例摘要

| 编号 | 标题 | 优先级 |
|------|------|--------|
| TC-LOGIN-001 | 手机号+验证码登录成功 | P1 |
| TC-LOGIN-002 | 验证码过期 | P0 |

## 注意事项
1. 验证码 **5 分钟** 有效。
2. 错误 **5 次** 锁定 **30 分钟**。

\`\`\`text
# 后续可接真实 SSE 流式输出
\`\`\`
`)

const previewHtml = computed(() => {
  const raw = marked.parse(markdownReport.value, { async: false })
  const html = typeof raw === 'string' ? raw : ''
  return DOMPurify.sanitize(html)
})

function handleSend() {
  const t = inputText.value.trim()
  if (!t) return
  mockMessages.value.push({
    id: String(Date.now()),
    role: 'user',
    content: t
  })
  inputText.value = ''
  mockMessages.value.push({
    id: String(Date.now() + 1),
    role: 'assistant',
    content: '（演示）已收到，真实环境将在此连接 SSE 并更新左侧输出区。'
  })
}

function handleSave() {
  // 演示
  console.info('save', editorJsonText.value)
}
</script>

<template>
  <div class="agent-page">
    <div class="agent-body">
      <!-- 左侧：输出区 -->
      <section class="agent-output">
        <div class="agent-output__toolbar">
          <span class="agent-output__title">输出区</span>
          <div class="agent-output__actions">
            <a-button type="primary" size="small" @click="handleSave">
              <template #icon>
                <SaveOutlined />
              </template>
              保存
            </a-button>
          </div>
        </div>

        <a-tabs v-model:activeKey="outputTab" class="agent-output__tabs" type="card">
          <a-tab-pane key="table">
            <template #tab>
              <span><UnorderedListOutlined /> 表格</span>
            </template>
            <div class="agent-output__pane agent-output__pane--table">
              <a-table
                :columns="tableColumns"
                :data-source="mockTestCases"
                :pagination="false"
                :scroll="{ x: 1100, y: 'calc(100vh - 320px)' }"
                size="small"
                bordered
              />
            </div>
          </a-tab-pane>

          <a-tab-pane key="editor">
            <template #tab>
              <span>编辑器</span>
            </template>
            <div class="agent-output__pane agent-output__pane--editor">
              <textarea
                v-model="editorJsonText"
                class="agent-editor"
                spellcheck="false"
                aria-label="JSON 编辑器"
              />
            </div>
          </a-tab-pane>

          <a-tab-pane key="preview">
            <template #tab>
              <span>预览</span>
            </template>
            <div class="agent-output__pane agent-output__pane--preview">
              <article class="markdown-body" v-html="previewHtml" />
            </div>
          </a-tab-pane>
        </a-tabs>
      </section>

      <!-- 右侧：对话区 -->
      <section class="agent-chat">
        <header class="agent-chat__header">
          <div class="agent-chat__title">
            <RobotOutlined class="agent-chat__title-icon" />
            <span>测试智能体</span>
          </div>
          <div class="agent-chat__header-actions">
            <a-button type="text" size="small" title="新会话">
              <PlusOutlined />
            </a-button>
            <a-button type="text" size="small" title="历史">
              <HistoryOutlined />
            </a-button>
          </div>
        </header>

        <div class="agent-chat__welcome" v-if="mockMessages.length === 0">
          <RobotOutlined class="agent-chat__welcome-icon" />
          <ul class="agent-chat__features">
            <li><CommentOutlined /> 文档生成</li>
            <li><ThunderboltOutlined /> 多轮对话</li>
            <li><UnorderedListOutlined /> 持续优化</li>
          </ul>
        </div>

        <div class="agent-chat__messages">
          <div
            v-for="m in mockMessages"
            :key="m.id"
            class="agent-msg"
            :class="m.role === 'user' ? 'agent-msg--user' : 'agent-msg--assistant'"
          >
            <a-avatar
              class="agent-msg__avatar"
              :style="{
                backgroundColor: m.role === 'user' ? '#1890ff' : '#52c41a'
              }"
            >
              {{ m.role === 'user' ? '我' : 'AI' }}
            </a-avatar>
            <div class="agent-msg__bubble">{{ m.content }}</div>
          </div>
        </div>

        <footer class="agent-chat__footer">
          <a-textarea
            v-model:value="inputText"
            :rows="3"
            placeholder="输入需求或修改说明，Enter 发送（Shift+Enter 换行）"
            class="agent-chat__input"
            @pressEnter.exact.prevent="handleSend"
          />
          <a-button type="primary" class="agent-chat__send" @click="handleSend">
            <template #icon>
              <SendOutlined />
            </template>
            发送
          </a-button>
        </footer>
      </section>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.agent-page {
  height: 100%;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.agent-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  background: #fff;
}

/* ---------- 左侧输出 ---------- */
.agent-output {
  flex: 1.25;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
  border-right: 1px solid #333;
}

.agent-output__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #252526;
  border-bottom: 1px solid #333;
}

.agent-output__title {
  font-weight: 600;
  font-size: 14px;
  color: #ccc;
}

.agent-output__tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;

  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 0 8px;
    background: #252526;
    border-bottom: 1px solid #333;

    &::before {
      border: none;
    }
  }

  :deep(.ant-tabs-tab) {
    color: #aaa !important;
    border: 1px solid transparent !important;
    background: transparent !important;

    &.ant-tabs-tab-active .ant-tabs-tab-btn {
      color: #fff !important;
    }
  }

  :deep(.ant-tabs-content-holder) {
    flex: 1;
    min-height: 0;
  }

  :deep(.ant-tabs-content) {
    height: 100%;
  }

  :deep(.ant-tabs-tabpane) {
    height: 100%;
  }
}

.agent-output__pane {
  height: calc(100vh - 280px);
  min-height: 360px;
  overflow: auto;
}

.agent-output__pane--table {
  padding: 12px;
  background: #fff;
  color: rgba(0, 0, 0, 0.85);

  :deep(.ant-table) {
    font-size: 12px;
  }
}

.agent-output__pane--editor {
  padding: 0;
  background: #1e1e1e;
}

.agent-editor {
  width: 100%;
  height: 100%;
  min-height: 360px;
  padding: 12px 16px;
  margin: 0;
  border: none;
  resize: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  background: #1e1e1e;
  outline: none;
}

.agent-output__pane--preview {
  padding: 16px 20px;
  background: #fff;
  color: #24292f;
}

.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  max-width: 720px;

  :deep(h1) {
    font-size: 1.35rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.35em;
    margin-top: 0;
  }

  :deep(h2) {
    font-size: 1.15rem;
    margin-top: 1em;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 13px;
  }

  :deep(th),
  :deep(td) {
    border: 1px solid #d0d7de;
    padding: 6px 10px;
  }

  :deep(th) {
    background: #f6f8fa;
  }

  :deep(pre) {
    background: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow: auto;
    font-size: 12px;
  }

  :deep(code) {
    font-family: Consolas, Monaco, monospace;
    font-size: 0.9em;
  }
}

/* ---------- 右侧对话 ---------- */
.agent-chat {
  flex: 0.85;
  min-width: 320px;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.agent-chat__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.agent-chat__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #262626;
}

.agent-chat__title-icon {
  font-size: 20px;
  color: #1890ff;
}

.agent-chat__header-actions {
  display: flex;
  gap: 4px;
}

.agent-chat__welcome {
  display: none;
}

.agent-chat__messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.agent-msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.agent-msg--user {
  flex-direction: row-reverse;

  .agent-msg__bubble {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
  }
}

.agent-msg__avatar {
  flex-shrink: 0;
}

.agent-msg__bubble {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #f0f0f0;
  font-size: 13px;
  line-height: 1.55;
  color: #434343;
  white-space: pre-wrap;
  word-break: break-word;
}

.agent-chat__footer {
  padding: 12px 16px 16px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agent-chat__input {
  resize: none;
}

.agent-chat__send {
  align-self: flex-end;
}
</style>
