import api from '@/utils/request'
import type { SkillMetaOut } from '@/schemas/skill'

export function listSkills() {
  return api.get<SkillMetaOut[]>('/skills')
}
