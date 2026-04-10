import { request } from '@/utils/request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  code: number
  message: string
  data: {
    access_token: string
    refresh_token: string
    user_info: {
      id: number
      username: string
      email: string | null
      nickname: string
      avatar_url: string | null
      phone: string | null
      status: number
      member_level: number
      member_level_display: string
      points: number
      is_vip: boolean
      vip_expired: boolean
      last_login_at: string
      last_login_ip: string
      created_at: string
      updated_at: string
    }
  }
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  code: number
  message: string
  data: {
    access_token: string
  }
}

// 登录
export function login(data: LoginRequest): Promise<LoginResponse> {
  return request({
    url: '/auth/login',
    method: 'POST',
    data
  })
}

// 刷新 Token
export function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  return request({
    url: '/auth/refresh',
    method: 'POST',
    data
  })
}
