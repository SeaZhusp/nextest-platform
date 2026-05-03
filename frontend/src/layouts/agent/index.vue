<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

/** true：左侧栏完全收起（滑出屏幕）；展开可通过左侧边缘「展开」按钮 */
const collapsed = ref(false)
const currentUser = computed(() => authStore.currentUser)

function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

function handleResize() {
  if (window.innerWidth < 768) {
    collapsed.value = true
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <a-layout style="min-height: 100vh">
    <Sidebar :collapsed="collapsed" :current-user="currentUser" />

    <!-- 侧栏展开时：收起按钮放在主内容区左缘（与顶栏「展开」对称） -->
    <a-button
      v-show="!collapsed"
      type="text"
      class="layout-sidebar-fold"
      aria-label="收起侧边栏"
      title="收起侧边栏"
      @click="toggleCollapsed"
    >
      <MenuFoldOutlined />
    </a-button>

    <a-button
      v-show="collapsed"
      type="text"
      class="layout-sidebar-expand"
      aria-label="展开侧边栏"
      title="展开侧边栏"
      @click="toggleCollapsed"
    >
      <MenuUnfoldOutlined />
    </a-button>

    <a-layout-content
      :style="{
        marginLeft: collapsed ? '0' : '260px',
        transition: 'margin-left 0.2s ease',
        padding: 0,
        minHeight: '100vh',
        background: '#f7fafc',
      }"
    >
      <router-view />
    </a-layout-content>
  </a-layout>
</template>

<style lang="scss" scoped>
.layout-sidebar-fold {
  position: fixed;
  left: 260px;
  top: 10px;
  z-index: 1001;
  width: 40px;
  height: 40px;
  padding: 0 !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.65) !important;
  background: #fff !important;
  border: 1px solid #f0f0f0 !important;
  border-right: none !important;
  border-radius: 8px 0 0 8px !important;
  box-shadow: -1px 1px 4px rgba(0, 0, 0, 0.06);
  transform: translateX(-100%);

  &:hover {
    color: #1890ff !important;
    background: #f5f5f5 !important;
    border-color: #f0f0f0 !important;
  }
}

.layout-sidebar-expand {
  position: fixed;
  left: 0;
  top: 10px;
  z-index: 1001;
  width: 40px;
  height: 40px;
  padding: 0 !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.65) !important;
  background: #fff !important;
  border: 1px solid #f0f0f0 !important;
  border-left: none !important;
  border-radius: 0 8px 8px 0 !important;
  box-shadow: 1px 1px 4px rgba(0, 0, 0, 0.06);

  &:hover {
    color: #1890ff !important;
    background: #f5f5f5 !important;
    border-color: #f0f0f0 !important;
  }
}
</style>
