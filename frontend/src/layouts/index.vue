<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminHeader from './components/Header.vue'
import AdminSidebar from './components/Sidebar.vue'
import TabView, { type TabItem } from './components/TabView.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 侧边栏折叠状态
const collapsed = ref(false)

// 标签页管理
const tabs = ref<TabItem[]>([])
const activeTabKey = ref('')

// 当前选中的菜单项
const selectedKeys = computed(() => {
  const activeMenu = route.meta?.activeMenu as string
  if (activeMenu) {
    return [activeMenu]
  }
  // 对于根路径，使用空字符串作为 key 来匹配仪表盘菜单项
  const currentPath = route.path || '/'
  const menuKey = currentPath === '/' ? '' : currentPath
  return [menuKey]
})

// 用户信息
const isLoggedIn = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.currentUser)

// 切换侧边栏折叠状态
function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

// 菜单点击处理
function handleMenuClick(info: { key: string }) {
  // 如果是空字符串（仪表盘），跳转到根路径
  const targetPath = info.key === '' ? '/' : info.key
  if (route.path !== targetPath) {
    router.push(targetPath)
  }
}

// 登出处理
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

// 添加标签页
function addTab(path: string, title: string, icon?: string) {
  
  const existingTab = tabs.value.find(tab => tab.path === path)
  if (existingTab) {
    activeTabKey.value = existingTab.key
    router.push(path)
    return
  }

  const newTab: TabItem = {
    key: path,
    title,
    path,
    closable: path !== '/', // 首页标签页不可关闭
    icon
  }

  tabs.value.push(newTab)
  activeTabKey.value = newTab.key
  router.push(path)
}

// 关闭标签页
function closeTab(key: string) {
  const tabIndex = tabs.value.findIndex(tab => tab.key === key)
  if (tabIndex === -1) return

  tabs.value.splice(tabIndex, 1)

  // 如果关闭的是当前标签页，切换到其他标签页
  if (activeTabKey.value === key) {
    if (tabs.value.length > 0) {
      const newActiveTab = tabs.value[Math.min(tabIndex, tabs.value.length - 1)]
      activeTabKey.value = newActiveTab.key
      router.push(newActiveTab.path)
    } else {
      // 如果没有标签页了，跳转到首页
      router.push('/')
    }
  }
}

// 关闭其他标签页
function closeOtherTabs(key: string) {
  const currentTab = tabs.value.find(tab => tab.key === key)
  if (!currentTab) return

  tabs.value = [currentTab]
  activeTabKey.value = currentTab.key
  router.push(currentTab.path)
}

// 关闭所有标签页
function closeAllTabs() {
  tabs.value = []
  activeTabKey.value = ''
  router.push('/')
}

// 刷新标签页
function refreshTab(_key: string) {
  // 这里可以实现页面刷新逻辑
  window.location.reload()
}

// 更新活动标签页
function updateActiveTabKey(key: string) {
  activeTabKey.value = key
}

// 监听路由变化，自动添加标签页
watch(() => route.path, (newPath) => {
  // 管理端项目的路由都是根路径下的子路由，排除登录页
  if (newPath !== '/login') {
    const title = route.meta?.title as string || '未知页面'
    const icon = route.meta?.icon as string
    addTab(newPath, title, icon)
  }
}, { immediate: true })

// 监听窗口大小变化
function handleResize() {
  if (window.innerWidth < 768) {
    collapsed.value = true
  }
}

// 监听关闭当前tab事件
function handleCloseCurrentTab(event: CustomEvent) {
  const currentPath = event.detail?.currentPath
  if (currentPath) {
    closeTab(currentPath)
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('closeCurrentTab', handleCloseCurrentTab as EventListener)
  handleResize() // 初始化时检查
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('closeCurrentTab', handleCloseCurrentTab as EventListener)
})

// 提供addTab方法给子组件使用
provide('addTab', addTab)
</script>

<template>
  <a-layout style="min-height: 100vh">
    <!-- 侧边栏 -->
    <AdminSidebar
      :collapsed="collapsed"
      :selectedKeys="selectedKeys"
      @menu-click="handleMenuClick"
    />
    
    <!-- 主内容区域 -->
    <a-layout>
      <!-- 顶部导航 -->
      <AdminHeader
        :collapsed="collapsed"
        :isLoggedIn="isLoggedIn"
        :currentUser="currentUser"
        @toggle-collapsed="toggleCollapsed"
        @logout="handleLogout"
      />
      
      <!-- 标签页区域 -->
      <div 
        v-if="tabs.length > 0"
        :style="{ 
          marginLeft: collapsed ? '80px' : '220px',
          transition: 'margin-left 0.2s',
          marginTop: '64px',
          position: 'fixed',
          top: 0,
          right: 0,
          left: 0,
          zIndex: 999,
          background: '#fff'
        }"
      >
        <TabView
          :tabs="tabs"
          :activeKey="activeTabKey"
          @updateActiveKey="updateActiveTabKey"
          @closeTab="closeTab"
          @closeOtherTabs="closeOtherTabs"
          @closeAllTabs="closeAllTabs"
          @refreshTab="refreshTab"
        />
      </div>
      
      <!-- 页面内容 -->
      <a-layout-content 
        :style="{ 
          marginLeft: collapsed ? '80px' : '220px',
          transition: 'margin-left 0.2s',
          padding: '12px',
          background: '#f7fafc',
          marginTop: tabs.length > 0 ? '104px' : '64px',
          minHeight: tabs.length > 0 ? 'calc(100vh - 104px)' : 'calc(100vh - 64px)'
        }"
      >
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style lang="scss" scoped>
// 布局样式
</style>
