import { createRouter, createWebHistory } from 'vue-router'
import AgentLayout from '@/layouts/agent/index.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', showInMenu: false }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/register/index.vue'),
    meta: { title: '注册', showInMenu: false }
  },
  // 后台管理路由（requiresAuth：登录即可；meta.role 与 localStorage user_info.user_type 一致）
  {
    path: '/',
    component: AgentLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页', icon: 'DashboardOutlined', showInMenu: true }
      },
      {
        path: 'agent',
        name: 'agent',
        component: () => import('@/views/agent/index.vue'),
        meta: { title: '测试助手', icon: 'RobotOutlined', showInMenu: false }
      },
      {
        path: 'hub/test-cases',
        name: 'hub-test-cases',
        component: () => import('@/views/hub/ComingSoon.vue'),
        meta: { title: '测试用例', icon: 'FileTextOutlined', showInMenu: true }
      },
      {
        path: 'hub/ui-test',
        name: 'hub-ui-test',
        component: () => import('@/views/hub/ComingSoon.vue'),
        meta: { title: 'UI测试', icon: 'DesktopOutlined', showInMenu: true }
      },
      {
        path: 'hub/api-test',
        name: 'hub-api-test',
        component: () => import('@/views/hub/ComingSoon.vue'),
        meta: { title: '接口测试', icon: 'ApiOutlined', showInMenu: true }
      },
      {
        path: 'hub/perf-test',
        name: 'hub-perf-test',
        component: () => import('@/views/hub/ComingSoon.vue'),
        meta: { title: '性能测试', icon: 'ThunderboltOutlined', showInMenu: true }
      },
      {
        path: 'agent-executions',
        name: 'agent-executions',
        component: () => import('@/views/agent-executions/index.vue'),
        meta: {
          title: '执行看板',
          icon: 'DashboardOutlined',
          showInMenu: false,
          activeMenu: '/agent'
        }
      },
      {
        path: '/llm',
        name: 'llm',
        component: () => import('@/views/llm/index.vue'),
        meta: { title: '模型配置', showInMenu: false }
      },
      {
        path: 'system',
        name: 'system',
        component: () => import('@/layouts/components/RouterOutlet.vue'),
        meta: {
          title: '系统管理',
          icon: 'SettingOutlined',
          showInMenu: true,
          role: 'admin'
        },
        children: [
          {
            path: 'users',
            name: 'users',
            component: () => import('@/views/system/users/index.vue'),
            meta: {
              title: '用户管理',
              icon: 'UserOutlined',
              showInMenu: true,
              role: 'admin'
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

function parseStoredUserInfo(raw: string): { user_type: string } | null {
  try {
    const u = JSON.parse(raw) as { user_type?: string }
    if (u && typeof u.user_type === 'string') {
      return { user_type: u.user_type }
    }
    return null
  } catch {
    return null
  }
}

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  const userInfoRaw = localStorage.getItem('user_info')

  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)

  if (needsAuth) {
    if (!token || !userInfoRaw) {
      next('/login')
      return
    }
    const user = parseStoredUserInfo(userInfoRaw)
    if (!user) {
      console.error('解析用户信息失败')
      next('/login')
      return
    }
    for (const record of to.matched) {
      const requiredRole = record.meta.role
      if (requiredRole && user.user_type !== requiredRole) {
        next('/')
        return
      }
    }
  }

  if ((to.path === '/login' || to.path === '/register') && token && userInfoRaw) {
    next('/agent')
    return
  }

  next()
})

export default router