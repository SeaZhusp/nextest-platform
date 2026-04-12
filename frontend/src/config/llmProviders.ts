/**
 * 模型提供商展示配置。
 *
 * 自定义图标：将你的 PNG/SVG/WebP 放到 `src/assets/llm-providers/`，
 * 文件名与下方 `id` 一致（如 `openai.svg`），构建时会打包进产物。
 *
 * - SVG/图片 URL：使用 `import xxx from '@/assets/llm-providers/xxx.svg?url'`
 * - 若某行去掉 `logo`，将使用 `fallbackIcon`（Ant Design 图标）
 */
import type { Component } from 'vue'
import {
  AppstoreOutlined,
  BulbOutlined,
  ExperimentOutlined,
  FireOutlined,
  ReadOutlined,
  ThunderboltOutlined
} from '@ant-design/icons-vue'

import logoAnthropic from '@/assets/llm-providers/anthropic.svg?url'
import logoDeepseek from '@/assets/llm-providers/deepseek.svg?url'
import logoOpenai from '@/assets/llm-providers/openai.svg?url'
import logoOther from '@/assets/llm-providers/other.svg?url'
import logoQwen from '@/assets/llm-providers/qwen.svg?url'
import logoZhipu from '@/assets/llm-providers/zhipu.svg?url'

export type LlmProviderId =
  | 'openai'
  | 'deepseek'
  | 'qwen'
  | 'zhipu'
  | 'anthropic'
  | 'other'

export interface LlmProviderItem {
  id: LlmProviderId
  label: string
  color: string
  logo?: string
  fallbackIcon: Component
}

export const PROVIDERS: LlmProviderItem[] = [
  { id: 'openai', label: 'OpenAI', color: '#10a37f', logo: logoOpenai, fallbackIcon: ExperimentOutlined },
  { id: 'deepseek', label: 'DeepSeek', color: '#4d6bfe', logo: logoDeepseek, fallbackIcon: ThunderboltOutlined },
  { id: 'qwen', label: '通义千问', color: '#ff6a00', logo: logoQwen, fallbackIcon: FireOutlined },
  { id: 'zhipu', label: '智谱', color: '#3468f7', logo: logoZhipu, fallbackIcon: BulbOutlined },
  { id: 'anthropic', label: 'Anthropic', color: '#d4a574', logo: logoAnthropic, fallbackIcon: ReadOutlined },
  { id: 'other', label: '其他', color: '#8c8c8c', logo: logoOther, fallbackIcon: AppstoreOutlined }
]

export const DEFAULT_BASE: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  anthropic: 'https://api.anthropic.com/v1',
  other: ''
}

export function providerMeta(id: string): LlmProviderItem {
  return PROVIDERS.find((p) => p.id === id) ?? PROVIDERS[PROVIDERS.length - 1]
}

export function providerLabel(id: string): string {
  return providerMeta(id).label
}
