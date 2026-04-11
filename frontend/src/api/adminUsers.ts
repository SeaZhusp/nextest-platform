import { request } from '@/utils/request'

export interface AdminUserRow {
  id: number
  username: string
  nickname: string | null
  email: string | null
  phone: string | null
  user_type: string
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface AdminUserListData {
  items: AdminUserRow[]
  total: number
  page: number
  size: number
}

export interface AdminUserListParams {
  page: number
  size: number
  username?: string
  is_active?: boolean
}

export interface AdminUserListResponse {
  code: number
  message: string
  data: AdminUserListData
}

export interface AdminUserActiveResponse {
  code: number
  message: string
  data: AdminUserRow
}

export function fetchAdminUserList(params: AdminUserListParams): Promise<AdminUserListResponse> {
  return request({
    url: '/admin/users',
    method: 'GET',
    params,
  })
}

export function setAdminUserActive(
  userId: number,
  is_active: boolean,
): Promise<AdminUserActiveResponse> {
  return request({
    url: `/admin/users/${userId}/active`,
    method: 'PATCH',
    data: { is_active },
  })
}

export function deleteAdminUser(userId: number): Promise<{ code: number; message: string; data: null }> {
  return request({
    url: `/admin/users/${userId}`,
    method: 'DELETE',
  })
}
