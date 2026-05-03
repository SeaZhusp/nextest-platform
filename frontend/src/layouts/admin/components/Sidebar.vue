<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Logo from '../../components/Logo.vue'
import {
  DashboardOutlined,
  ShoppingOutlined,
  UserOutlined,
  SettingOutlined,
  AppstoreOutlined,
  TeamOutlined,
  RobotOutlined,
  ShopOutlined
} from '@ant-design/icons-vue'

export interface MenuItem {
  key: string
  label: string
  icon?: any
  children?: MenuItem[]
}

interface Props {
  collapsed: boolean
  selectedKeys: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  menuClick: [info: { key: string }]
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

function canSeeRouteMeta(meta: Record<string, unknown> | undefined): boolean {
  const role = meta?.role as string | undefined
  if (!role) {
    return true
  }
  return authStore.currentUser?.user_type === role
}

// 图标映射
const iconMap: Record<string, any> = {
  'DashboardOutlined': DashboardOutlined,
  'ShoppingOutlined': ShoppingOutlined,
  'UserOutlined': UserOutlined,
  'SettingOutlined': SettingOutlined,
  'AppstoreOutlined': AppstoreOutlined,
  'TeamOutlined': TeamOutlined,
  'RobotOutlined': RobotOutlined,
  'ShopOutlined': ShopOutlined
}

function joinRoutePath(base: string, segment: string) {
  const b = base.replace(/\/$/, '') || '/admin'
  const s = segment.replace(/^\//, '')
  if (!s) return b
  return `${b}/${s}`
}

// 从路由配置构建菜单项（与 /admin 下子路由一致）
const menuItems = computed<MenuItem[]>(() => {
  const options = (router as any).options?.routes || []
  const adminRoute = options.find((r: any) => r.path === '/admin')
  const basePath = '/admin'
  const children = (adminRoute?.children || []) as any[]

  return children
    .filter((r: any) => r.meta?.showInMenu !== false && canSeeRouteMeta(r.meta))
    .map((r: any) => {
      const rawPath: string = r.path || ''
      const key = rawPath === '' ? basePath : joinRoutePath(basePath, rawPath)
      const label: string = r.meta?.title || r.name || key
      const iconName = r.meta?.icon
      const icon = iconName ? iconMap[iconName] : undefined

      // 如果有子菜单，递归处理
      const childRoutes = r.children || []
      const subChildren = childRoutes
        .filter(
          (child: any) =>
            child.meta?.showInMenu !== false && canSeeRouteMeta(child.meta)
        )
        .map((child: any) => {
          const childPath: string = child.path || ''
          const childKey = childPath === '' ? key : joinRoutePath(key, childPath)
          const childLabel: string = child.meta?.title || child.name || childKey
          return { key: childKey, label: childLabel }
        })
      
      if (subChildren.length === 0 && childRoutes.length > 0) {
        return null
      }

      return {
        key,
        label,
        icon,
        children: subChildren.length > 0 ? subChildren : undefined
      }
    })
    .filter((item): item is NonNullable<typeof item> => item !== null)
})

// 计算当前应该展开的菜单
const openKeys = ref<string[]>([])

// 根据当前路由计算需要展开的菜单
const computeOpenKeys = () => {
  const currentPath = route.path
  const keys: string[] = []
  
  // 遍历菜单项，找到包含当前路径的父菜单
  menuItems.value.forEach(item => {
    if (item.children) {
      const hasActiveChild = item.children.some(child => {
        // 精确匹配
        if (currentPath === child.key) {
          return true
        }
        // 检查当前路径是否以子菜单键开头（用于子页面）
        if (currentPath.startsWith(child.key + '/')) {
          return true
        }
        return false
      })
      
      // 检查当前路径是否属于该菜单项的子路径
      // 例如：/goods/add 应该展开 /goods 菜单
      if (currentPath.startsWith(item.key + '/')) {
        keys.push(item.key)
        return
      }
      
      if (hasActiveChild) {
        keys.push(item.key)
      }
    }
  })
  
  return keys
}

// 监听路由变化，更新展开的菜单
watch(() => route.path, () => {
  if (!props.collapsed) {
    openKeys.value = computeOpenKeys()
  }
}, { immediate: true })

// 监听折叠状态变化
watch(() => props.collapsed, (collapsed) => {
  if (collapsed) {
    openKeys.value = []
  } else {
    openKeys.value = computeOpenKeys()
  }
})

function handleMenuClick(info: { key: string }) {
  emit('menuClick', info)
}
</script>

<template>
  <a-layout-sider
    :collapsed="collapsed"
    :width="260"
    :collapsedWidth="80"
    class="sidebar"
    :style="{
      position: 'fixed',
      left: 0,
      top: 0,
      bottom: 0,
      zIndex: 999
    }"
  >
    <Logo class="sidebar-logo-wrap" />

    <!-- 菜单区域 -->
    <a-menu
      :selectedKeys="selectedKeys"
      :openKeys="collapsed ? [] : openKeys"
      mode="inline"
      :inlineCollapsed="collapsed"
      class="sidebar-menu"
      @click="handleMenuClick"
    >
      <template v-for="item in menuItems" :key="item.key">
        <!-- 有子菜单的情况 -->
        <a-sub-menu v-if="item.children" :key="'sub-' + item.key">
          <template #title>
            <component :is="item.icon" v-if="item.icon" />
            <span>{{ item.label }}</span>
          </template>
          <a-menu-item 
            v-for="child in item.children" 
            :key="child.key"
          >
            {{ child.label }}
          </a-menu-item>
        </a-sub-menu>
        
        <!-- 没有子菜单的情况（key 须为真实 path，供 @click 导航；与 sub- 前缀区分避免与 v-if 分支 key 冲突） -->
        <a-menu-item v-else :key="item.key">
          <component :is="item.icon" v-if="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </template>
    </a-menu>
  </a-layout-sider>
</template>

<style lang="scss" scoped>
.sidebar {
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

.sidebar-logo-wrap {
  flex-shrink: 0;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-menu {
  border: none;
  background: #fff;
  
  :deep(.ant-menu-item) {
    color: rgba(0, 0, 0, 0.85);
    margin: 4px 8px;
    height: 40px;
    line-height: 40px;
    padding-left: 24px !important;
    border-radius: 6px;
    
    &:hover {
      color: #1890ff !important;
      background: #f0f8ff !important;
    }
    
    &.ant-menu-item-selected {
      color: #1890ff !important;
      background: #f0f8ff !important;
      
      &::after {
        display: none;
      }
    }
  }
  
  :deep(.ant-menu-submenu) {
    color: rgba(0, 0, 0, 0.85);
    
    .ant-menu-submenu-title {
      color: rgba(0, 0, 0, 0.85) !important;
      height: 40px;
      line-height: 40px;
      margin: 4px 8px;
      padding-left: 24px !important;
      border-radius: 6px;
      
      &:hover {
        color: #1890ff !important;
        background: #f0f8ff !important;
      }
    }
    
    &.ant-menu-submenu-open > .ant-menu-submenu-title {
      color: #1890ff !important;
    }
  }
  
  :deep(.ant-menu-sub) {
    background: #fafafa;
    
    .ant-menu-item {
      color: rgba(0, 0, 0, 0.85) !important;
      padding-left: 48px !important;
      margin: 2px 8px;
      height: 36px;
      line-height: 36px;
      border-radius: 6px;
      
      &:hover {
        color: #1890ff !important;
        background: #f0f8ff !important;
      }
      
      &.ant-menu-item-selected {
        color: #1890ff !important;
        background: #f0f8ff !important;
      }
    }
  }
}

// 折叠状态下的样式调整
:deep(.ant-layout-sider-collapsed) {
  .sidebar-menu {
    :deep(.ant-menu-item),
    :deep(.ant-menu-submenu-title) {
      padding: 0 24px;
      text-align: center;
    }
  }
}
</style>