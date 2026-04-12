import api from '@/utils/request'
import type { SkillPlazaListData } from '@/schemas/skill'

export function listSkillPlaza(params: { page?: number; size?: number; q?: string }) {
  return api.get<SkillPlazaListData>('/skill-plaza', { params })
}
