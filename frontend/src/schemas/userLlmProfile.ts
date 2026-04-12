/** 对齐后端 app/schemas/user_llm_profile.py */

export type LlmProviderId = 'openai' | 'deepseek' | 'qwen' | 'zhipu' | 'anthropic' | 'other'

export interface UserLlmProfileOut {
  id: number
  provider: string
  display_name: string
  api_base: string
  model_name: string
  key_last4: string
  api_key_masked: string
  is_active: boolean
}

export interface UserLlmProfileDetail extends UserLlmProfileOut {
  api_key: string
}

export interface UserLlmProfileListResponse {
  items: UserLlmProfileOut[]
}

export interface UserLlmProfileCreate {
  provider: string
  display_name?: string
  api_base: string
  model_name: string
  api_key: string
  is_active?: boolean
}

export interface UserLlmProfileUpdate {
  provider?: string
  display_name?: string
  api_base?: string
  model_name?: string
  api_key?: string
  is_active?: boolean
}

export interface LlmConnectionTestRequest {
  api_base: string
  model_name: string
  api_key: string
}

export interface LlmConnectionTestResult {
  ok: boolean
  message: string
}
