# Agent SSE 协议（`POST /api/agent/chat/stream`）

**版本**：1.0  
**内容类型**：`text/event-stream; charset=utf-8`  
**请求体**：与 `POST /api/agent/chat` 相同（`AgentChatRequest`，JSON）。

## 帧格式

每条事件由若干行组成，以空行结束：

```http
event: <事件名>
data: <JSON 对象>

```

- `event` 与 `data` 均为单行；`data` 为 **UTF-8 JSON 字符串**（可含中文）。
- 客户端应按 **SSE 规范** 解析（按 `\n\n` 分帧，再解析 `event:` / `data:`）。

## 事件类型

| event | data 说明 |
|-------|-----------|
| `token` | `{"text": string}` — 模型输出增量（仅 `test_case_gen` 且已配置 `LLM_API_KEY` 时出现）。 |
| `done` | 结束帧，含完整业务结果，字段见下表。 |
| `error` | `{"message": string, "details"?: object}` — 失败原因（如 JSON 解析失败）。 |

### `done.data` 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | string | 会话 ID（未传则服务端新建 UUID）。 |
| `skill_id` | string | 使用的技能 ID。 |
| `parts` | array | 规范化后的用户输入片段（与同步接口一致）。 |
| `test_cases` | array | 结构化用例列表（`TestCaseItem` 数组）。 |
| `used_template` | boolean, 可选 | `true` 表示未走 LLM（无密钥或非流式模板路径）。 |

## 与同步接口的关系

- **`POST /api/agent/chat`**：一次 JSON 返回，适合简单客户端；内部仍走技能 +（若配置）LLM。
- **`POST /api/agent/chat/stream`**：先推送 `token`（若启用 LLM），最后 **`done`** 中带 `test_cases`；若解析失败则只发 **`error`**，不发 `done`。

## 鉴权

请求头需携带 `Authorization: Bearer <access_token>`，与同步接口一致。
