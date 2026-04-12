/** GET /api/skills — 运行时已注册技能元数据 */
export interface SkillMetaOut {
  skill_id: string
  name: string
  version: string
  description?: string
}

/** 技能目录 DB（广场 + /admin/skills） */

export interface SkillPlazaItem {
  id: number
  skill_id: string
  name: string
  description: string
  capability_tags: string[]
  icon_key?: string | null
  is_published: boolean
  sort_order: number
  use_count: number
  runtime_available: boolean
}

export interface SkillPlazaListData {
  items: SkillPlazaItem[]
  total: number
  page: number
  size: number
}

export type SkillAdmin = SkillPlazaItem & {
  created_at: string
  updated_at: string
}

export interface SkillAdminListData {
  items: SkillAdmin[]
  total: number
  page: number
  size: number
}
