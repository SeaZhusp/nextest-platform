import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, refreshToken as refreshTokenApi } from '@/api/auth'

export interface User {
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

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const currentUser = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!accessToken.value && !!currentUser.value)

  // 初始化 - 从 localStorage 恢复状态
  function init() {
    const storedToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user_info')

    if (storedToken) {
      accessToken.value = storedToken
    }
    if (storedRefreshToken) {
      refreshToken.value = storedRefreshToken
    }
    if (storedUser) {
      try {
        currentUser.value = JSON.parse(storedUser)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        clearAuth()
      }
    }
  }

  // 设置认证信息
  function setAuth(user: User, accessTokenValue: string, refreshTokenValue?: string) {
    currentUser.value = user
    accessToken.value = accessTokenValue
    
    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue
    }

    // 持久化到 localStorage
    localStorage.setItem('access_token', accessTokenValue)
    localStorage.setItem('user_info', JSON.stringify(user))
    
    if (refreshTokenValue) {
      localStorage.setItem('refresh_token', refreshTokenValue)
    }
  }

  // 清除认证信息
  function clearAuth() {
    currentUser.value = null
    accessToken.value = null
    refreshToken.value = null

    // 清除 localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  // 登录
  async function login(credentials: { username: string; password: string }) {
    try {
      const response = await loginApi(credentials)
      
      if (response.code === 200) {
        const { access_token, refresh_token, user_info } = response.data
        
        setAuth(user_info, access_token, refresh_token)
        
        return { user: user_info, accessToken: access_token }
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 登出
  async function logout() {
    clearAuth()
  }

  // 刷新 Token
  async function refreshAccessToken() {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }

      const response = await refreshTokenApi({ refresh_token: refreshToken.value })
      
      if (response.code === 200) {
        const newAccessToken = response.data.access_token
        accessToken.value = newAccessToken
        localStorage.setItem('access_token', newAccessToken)
        
        return newAccessToken
      } else {
        throw new Error(response.message || '刷新 Token 失败')
      }
    } catch (error) {
      console.error('刷新 Token 失败:', error)
      clearAuth()
      throw error
    }
  }

  // 初始化状态
  init()

  return {
    // 状态
    currentUser,
    accessToken,
    refreshToken,
    
    // 计算属性
    isAuthenticated,
    
    // 方法
    clearAuth,
    login,
    logout,
    refreshAccessToken
  }
})
