import { request } from '@/utils/request'

export type ProjectParticipation = 'all' | 'owned' | 'joined'

export interface ProjectRow {
  id: number
  name: string
  description: string | null
  owner_id: number
  /** 负责人展示名（昵称优先） */
  owner_name: string
  my_role: 'owner' | 'leader' | 'tester' | string
  created_at: string
  updated_at: string
}

export interface ProjectMemberRow {
  user_id: number
  username: string
  nickname: string | null
  role: string
}

export interface ProjectMemberListData {
  items: ProjectMemberRow[]
}

export interface ProjectMemberListResponse {
  code: number
  message: string
  data: ProjectMemberListData
}

export function fetchProjectMembers(projectId: number): Promise<ProjectMemberListResponse> {
  return request({
    url: `/projects/${projectId}/members`,
    method: 'GET',
  })
}

export interface ProjectMemberAddBody {
  username: string
  role: 'leader' | 'tester'
}

export interface ProjectMemberOutResponse {
  code: number
  message: string
  data: ProjectMemberRow
}

export function addProjectMember(
  projectId: number,
  body: ProjectMemberAddBody,
): Promise<ProjectMemberOutResponse> {
  return request({
    url: `/projects/${projectId}/members`,
    method: 'POST',
    data: body,
  })
}

export function removeProjectMember(
  projectId: number,
  memberUserId: number,
): Promise<{ code: number; message: string; data: null }> {
  return request({
    url: `/projects/${projectId}/members/${memberUserId}`,
    method: 'DELETE',
  })
}

export interface ProjectListData {
  items: ProjectRow[]
  total: number
  page: number
  size: number
}

export interface ProjectListParams {
  page: number
  size: number
  participation?: ProjectParticipation
}

export interface ProjectListResponse {
  code: number
  message: string
  data: ProjectListData
}

export function fetchProjectList(params: ProjectListParams): Promise<ProjectListResponse> {
  return request({
    url: '/projects',
    method: 'GET',
    params,
  })
}

export interface ProjectCreateBody {
  name: string
  description?: string | null
}

export interface ProjectOutResponse {
  code: number
  message: string
  data: ProjectRow
}

export function createProject(body: ProjectCreateBody): Promise<ProjectOutResponse> {
  return request({
    url: '/projects',
    method: 'POST',
    data: body,
  })
}

export interface ProjectUpdateBody {
  name?: string
  description?: string | null
}

export function updateProject(
  projectId: number,
  body: ProjectUpdateBody,
): Promise<ProjectOutResponse> {
  return request({
    url: `/projects/${projectId}`,
    method: 'PATCH',
    data: body,
  })
}

export function deleteProject(projectId: number): Promise<{ code: number; message: string; data: null }> {
  return request({
    url: `/projects/${projectId}`,
    method: 'DELETE',
  })
}

export function fetchProject(projectId: number): Promise<ProjectOutResponse> {
  return request({
    url: `/projects/${projectId}`,
    method: 'GET',
  })
}
