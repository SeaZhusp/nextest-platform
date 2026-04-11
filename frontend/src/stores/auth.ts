import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  login as loginApi,
  register as registerApi,
  refreshToken as refreshTokenApi,
} from '@/api/auth'
import type { AuthUserInfo, RegisterRequest } from '@/api/auth'

export type User = AuthUserInfo

function isSuccessCode(code: number | undefined): boolean {
  return code === 200 || code === 0
}

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!currentUser.value)

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

  function setAuth(user: User, accessTokenValue: string, refreshTokenValue?: string) {
    currentUser.value = user
    accessToken.value = accessTokenValue

    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue
    }

    localStorage.setItem('access_token', accessTokenValue)
    localStorage.setItem('user_info', JSON.stringify(user))

    if (refreshTokenValue) {
      localStorage.setItem('refresh_token', refreshTokenValue)
    }
  }

  function clearAuth() {
    currentUser.value = null
    accessToken.value = null
    refreshToken.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  async function login(credentials: { username: string; password: string }) {
    const response = await loginApi(credentials)

    if (!isSuccessCode(response.code) || !response.data) {
      throw new Error(response.message || '登录失败')
    }

    const { access_token, refresh_token, user_info } = response.data
    setAuth(user_info, access_token, refresh_token)
    return { user: user_info, accessToken: access_token }
  }

  async function register(payload: RegisterRequest) {
    const response = await registerApi(payload)

    if (!isSuccessCode(response.code) || !response.data) {
      throw new Error(response.message || '注册失败')
    }

    const { access_token, refresh_token, user_info } = response.data
    setAuth(user_info, access_token, refresh_token)
    return { user: user_info, accessToken: access_token }
  }

  async function logout() {
    clearAuth()
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('没有刷新令牌')
    }

    const response = await refreshTokenApi({ refresh_token: refreshToken.value })

    if (!isSuccessCode(response.code) || !response.data) {
      throw new Error(response.message || '刷新 Token 失败')
    }

    const newAccessToken = response.data.access_token
    accessToken.value = newAccessToken
    localStorage.setItem('access_token', newAccessToken)

    if (response.data.refresh_token) {
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('refresh_token', response.data.refresh_token)
    }

    return newAccessToken
  }

  init()

  return {
    currentUser,
    accessToken,
    refreshToken,
    isAuthenticated,
    clearAuth,
    login,
    register,
    logout,
    refreshAccessToken,
  }
})
