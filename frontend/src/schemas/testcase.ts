/** 与后端 app/schemas/testcase.py 对齐 */
export interface TestCaseItem {
  id?: string | null
  case_no: string
  module: string
  title: string
  preconditions?: string
  steps?: string
  expected?: string
  priority?: string
}

/**
 * 将 API/模型可能返回的 string | string[]、或整段 JSON 数组字符串，
 * 规范为表格单元格内多行文本（换行分隔），避免界面出现 `['1.', …]` 的 Python 列表字面量。
 */
export function multilineFieldFromApi(value: unknown): string {
  if (value == null) return ''
  if (Array.isArray(value)) {
    return value
      .map((x) => String(x).trim())
      .filter(Boolean)
      .join('\n')
  }
  const s = String(value).trim()
  if (!s) return ''
  if (s.startsWith('[')) {
    try {
      const parsed = JSON.parse(s) as unknown
      if (Array.isArray(parsed)) {
        return parsed
          .map((x) => String(x).trim())
          .filter(Boolean)
          .join('\n')
      }
    } catch {
      /* 非 JSON（如 Python 单引号列表）留给后端已持久化数据；必要时用户可手动改一格 */
    }
  }
  return s
}
