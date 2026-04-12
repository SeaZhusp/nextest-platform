import api from '@/utils/request'
import type {
  LlmConnectionTestRequest,
  LlmConnectionTestResult,
  UserLlmProfileCreate,
  UserLlmProfileDetail,
  UserLlmProfileListResponse,
  UserLlmProfileOut,
  UserLlmProfileUpdate
} from '@/schemas/userLlmProfile'

export function listUserLlmProfiles(params?: { active_only?: boolean }) {
  return api.get<UserLlmProfileListResponse>('/user/llm-profiles', { params })
}

export function getUserLlmProfile(id: number) {
  return api.get<UserLlmProfileDetail>(`/user/llm-profiles/${id}`)
}

export function createUserLlmProfile(body: UserLlmProfileCreate) {
  return api.post<UserLlmProfileOut>('/user/llm-profiles', body)
}

export function updateUserLlmProfile(id: number, body: UserLlmProfileUpdate) {
  return api.patch<UserLlmProfileOut>(`/user/llm-profiles/${id}`, body)
}

export function setUserLlmProfileActive(id: number, is_active: boolean) {
  return api.patch<UserLlmProfileOut>(`/user/llm-profiles/${id}/active`, { is_active })
}

export function deleteUserLlmProfile(id: number) {
  return api.delete(`/user/llm-profiles/${id}`)
}

export function testLlmConnection(body: LlmConnectionTestRequest) {
  return api.post<LlmConnectionTestResult>('/user/llm-profiles/test', body)
}

export function testLlmConnectionById(id: number) {
  return api.post<LlmConnectionTestResult>(`/user/llm-profiles/${id}/test`, {})
}
