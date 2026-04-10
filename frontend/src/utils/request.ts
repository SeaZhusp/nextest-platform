import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import axios from 'axios'
import { message } from 'ant-design-vue'

// 后端统一返回格式
export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
  timestamp?: string
}

// 获取Token
function getToken(): string | null {
  return localStorage.getItem('access_token')
}

// 退出登录
function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_info')
  
  // 跳转到登录页面
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

// 创建axios实例
const instance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加Token
instance.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.token = `${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 统一处理错误
instance.interceptors.response.use(
  (response) => {
    const data = response.data
    
    // 二进制数据直接返回
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return data
    }
    
    // 处理业务状态码
    if (data.code !== undefined) {
      if (data.code === 200 || data.code === 0) {
        return data
      } else if (data.code === 401) {
        message.error(data.message || '认证失败，请重新登录')
        handleLogout()
        return Promise.reject(new Error(data.message))
      } else {
        message.error(data.message || `请求失败 (${data.code})`)
        return Promise.reject(new Error(data.message))
      }
    }
    
    return data
  },
  (error) => {
    // HTTP错误处理
    if (error.response) {
      const { status, data } = error.response
      const errorMsg = data?.message || `请求失败 (${status})`
      
      if (status === 401) {
        message.error('认证失败，请重新登录')
        handleLogout()
      } else if (status === 403) {
        message.warning('权限不足')
      } else if (status === 404) {
        message.warning('请求的资源不存在')
      } else if (status >= 500) {
        message.error('服务器错误，请稍后重试')
      } else {
        message.error(errorMsg)
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// 通用请求方法
const request = <T = any>(config: AxiosRequestConfig): Promise<T> => {
  return instance(config)
}

// 便捷方法
const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => 
    request({ ...config, method: 'GET', url }),
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => 
    request({ ...config, method: 'POST', url, data }),
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => 
    request({ ...config, method: 'PUT', url, data }),
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => 
    request({ ...config, method: 'DELETE', url }),
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => 
    request({ ...config, method: 'PATCH', url, data }),
}

export { request, api }
export default api
