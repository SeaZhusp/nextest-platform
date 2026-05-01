/** GET /api/skills — 运行时已注册技能元数据 */
export interface SkillMetaOut {
  skill_id: string
  name: string
  version: string
  description?: string
  default_render?: 'table' | 'markdown' | 'mindmap'
  render_modes?: Array<'table' | 'markdown' | 'mindmap'>
}
