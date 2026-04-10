import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layouts/index.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '管理员登录', showInMenu: false }
  },
  // 后台管理路由
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'DashboardOutlined' }
      },
      {
        path: 'system',
        name: 'system',
        meta: { 
          title: '系统管理',
          icon: 'SettingOutlined',
          showInMenu: true
        },
        children: [
          {
            path: 'users',
            name: 'users',
            component: () => import('@/views/system/users/index.vue'),
            meta: {
              title: '用户管理',
              icon: 'UserOutlined',
              showInMenu: true
            }
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('user_info')
  
  // 检查是否需要管理员权限
  if (to.meta?.requiresAuth && to.meta?.role === 'admin') {
    if (!token || !userInfo) {
      // 未登录，重定向到管理端登录页面
      next('/login')
      return
    }
    
    // 可以在这里添加更详细的角色验证
    try {
      JSON.parse(userInfo) // 验证用户信息格式
      // 这里可以检查用户角色是否为管理员
      // if (user.role !== 'admin') {
      //   next('/login')
      //   return
      // }
    } catch (error) {
      console.error('解析用户信息失败:', error)
      next('/login')
      return
    }
  }
  
  // 如果已经登录且访问登录页面，重定向到管理后台
  if (to.path === '/login' && token && userInfo) {
    next('/')
    return
  }
  
  next()
})

export default router