import { request } from '@/utils/request'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  password_confirm: string
}

/** 与后端 `UserPublic`（登录/注册 `data.user_info`）一致 */
export interface AuthUserInfo {
  id: number
  username: string
  email: string | null
  nickname: string | null
  phone: string | null
  role: string
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface AuthSessionPayload {
  access_token: string
  refresh_token: string
  token_type: string
  user_info: AuthUserInfo
}

export interface AuthSessionResponse {
  code: number
  message: string
  data: AuthSessionPayload
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  code: number
  message: string
  data: {
    access_token: string
    refresh_token: string
    token_type?: string
  }
}

export function login(data: LoginRequest): Promise<AuthSessionResponse> {
  return request({
    url: '/auth/login',
    method: 'POST',
    data,
  })
}

export function register(data: RegisterRequest): Promise<AuthSessionResponse> {
  return request({
    url: '/auth/register',
    method: 'POST',
    data,
  })
}

export function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  return request({
    url: '/auth/refresh',
    method: 'POST',
    data,
  })
}
