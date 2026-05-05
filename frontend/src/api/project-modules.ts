import { request, type ApiResponse } from '@/utils/request'

/** 与后端 ProjectModuleOut 一致，供功能/接口/UI 等模块共用 */
export interface ProjectModuleNode {
  id: number
  project_id: number
  parent_id: number | null
  name: string
  sort_order: number
  description: string | null
  created_at: string
  updated_at: string
  children: ProjectModuleNode[]
}

export interface ProjectModuleTreeData {
  roots: ProjectModuleNode[]
}

export type ProjectModuleTreeResponse = ApiResponse<ProjectModuleTreeData>

export function fetchProjectModuleTree(projectId: number): Promise<ProjectModuleTreeResponse> {
  return request({
    url: `/projects/${projectId}/modules/tree`,
    method: 'GET',
  })
}

export interface ProjectModuleCreateBody {
  name: string
  parent_id?: number | null
  sort_order?: number | null
  description?: string | null
}

export type ProjectModuleDetailResponse = ApiResponse<ProjectModuleNode>

export function createProjectModule(
  projectId: number,
  body: ProjectModuleCreateBody,
): Promise<ProjectModuleDetailResponse> {
  return request({
    url: `/projects/${projectId}/modules`,
    method: 'POST',
    data: body,
  })
}

export interface ProjectModuleUpdateBody {
  name?: string
  parent_id?: number | null
  sort_order?: number | null
  description?: string | null
}

export function updateProjectModule(
  projectId: number,
  moduleId: number,
  body: ProjectModuleUpdateBody,
): Promise<ProjectModuleDetailResponse> {
  return request({
    url: `/projects/${projectId}/modules/${moduleId}`,
    method: 'PATCH',
    data: body,
  })
}

export function deleteProjectModule(
  projectId: number,
  moduleId: number,
): Promise<{ code: number; message: string; data: null }> {
  return request({
    url: `/projects/${projectId}/modules/${moduleId}`,
    method: 'DELETE',
  })
}

/** 某节点及其所有后代 id（移动父级时不可选自身与子节点） */
export function collectModuleSubtreeIds(roots: ProjectModuleNode[], moduleId: number): Set<number> {
  const byId = new Map<number, ProjectModuleNode>()
  function index(nodes: ProjectModuleNode[]) {
    for (const n of nodes) {
      byId.set(n.id, n)
      if (n.children?.length) index(n.children)
    }
  }
  index(roots)
  const out = new Set<number>()
  function walk(id: number) {
    out.add(id)
    const n = byId.get(id)
    if (!n?.children?.length) return
    for (const ch of n.children) walk(ch.id)
  }
  walk(moduleId)
  return out
}

export function projectModuleRootsToTreeSelectDataExcluding(
  roots: ProjectModuleNode[],
  excludeIds: Set<number>,
): ProjectModuleTreeSelectNode[] {
  function convert(nodes: ProjectModuleNode[]): ProjectModuleTreeSelectNode[] {
    const result: ProjectModuleTreeSelectNode[] = []
    for (const r of nodes) {
      if (excludeIds.has(r.id)) continue
      const rawChildren = r.children?.length ? convert(r.children) : undefined
      const children = rawChildren?.length ? rawChildren : undefined
      result.push({
        title: r.name,
        value: r.id,
        children,
      })
    }
    return result
  }
  return convert(roots)
}

/** Ant Design Tree 节点（key 使用模块 id 字符串） */
export interface ProjectModuleAntTreeNode {
  key: string
  title: string
  children?: ProjectModuleAntTreeNode[]
}

export function projectModuleRootsToAntTreeData(roots: ProjectModuleNode[]): {
  treeData: ProjectModuleAntTreeNode[]
  keyToModule: Map<string, ProjectModuleNode>
} {
  const keyToModule = new Map<string, ProjectModuleNode>()

  function convert(nodes: ProjectModuleNode[]): ProjectModuleAntTreeNode[] {
    return nodes.map((m) => {
      const key = String(m.id)
      keyToModule.set(key, m)
      const children = m.children?.length ? convert(m.children) : undefined
      return {
        key,
        title: m.name,
        children,
      }
    })
  }

  return { treeData: convert(roots), keyToModule }
}

/** a-tree-select 默认字段 title / value / children */
export interface ProjectModuleTreeSelectNode {
  title: string
  value: number
  children?: ProjectModuleTreeSelectNode[]
}

export function projectModuleRootsToTreeSelectData(
  roots: ProjectModuleNode[],
): ProjectModuleTreeSelectNode[] {
  return roots.map((r) => ({
    title: r.name,
    value: r.id,
    children: r.children?.length ? projectModuleRootsToTreeSelectData(r.children) : undefined,
  }))
}

export function collectTreeKeys(nodes: ProjectModuleAntTreeNode[]): string[] {
  const keys: string[] = []
  function walk(list: ProjectModuleAntTreeNode[]) {
    for (const n of list) {
      keys.push(n.key)
      if (n.children?.length) {
        walk(n.children)
      }
    }
  }
  walk(nodes)
  return keys
}
