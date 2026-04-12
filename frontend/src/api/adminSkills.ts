import api from '@/utils/request'
import type { SkillAdmin, SkillAdminListData } from '@/schemas/skill'

export function listAdminSkills(params: { page?: number; size?: number; q?: string }) {
  return api.get<SkillAdminListData>('/admin/skills', { params })
}

export function createSkill(body: Record<string, unknown>) {
  return api.post<SkillAdmin>('/admin/skills', body)
}

export function updateSkill(recordId: number, body: Record<string, unknown>) {
  return api.put<SkillAdmin>(`/admin/skills/${recordId}`, body)
}

export function deleteSkill(recordId: number) {
  return api.delete(`/admin/skills/${recordId}`)
}
