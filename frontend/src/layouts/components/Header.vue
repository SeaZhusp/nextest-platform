<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import type { AuthUserInfo } from '@/api/auth'

interface Props {
  collapsed: boolean
  isLoggedIn: boolean
  currentUser: AuthUserInfo | null
}

defineProps<Props>()

const route = useRoute()

// 当前页面标题
const currentPageTitle = computed(() => {
  return (route.meta?.title as string) || '首页'
})

const emit = defineEmits<{
  toggleCollapsed: []
  logout: []
}>()

const userMenuVisible = ref(false)

function handleToggleCollapsed() {
  emit('toggleCollapsed')
}

function handleLogout() {
  emit('logout')
  userMenuVisible.value = false
}

</script>

<template>
  <a-layout-header 
    class="header"
    :style="{ 
      marginLeft: collapsed ? '80px' : '220px',
      transition: 'margin-left 0.2s'
    }"
  >
    <div class="header-content">
      <!-- 左侧：折叠按钮 -->
      <div class="header-left">
        <a-button 
          type="text" 
          @click="handleToggleCollapsed"
          class="collapse-btn"
        >
          <MenuUnfoldOutlined v-if="collapsed" />
          <MenuFoldOutlined v-else />
        </a-button>
        
        <a-breadcrumb class="breadcrumb">
          <a-breadcrumb-item>管理后台</a-breadcrumb-item>
          <a-breadcrumb-item>{{ currentPageTitle }}</a-breadcrumb-item>
        </a-breadcrumb>
      </div>

      <!-- 右侧：用户信息和操作 -->
      <div class="header-right">
        <!-- 通知 -->
        <a-badge :count="5" :offset="[10, 0]">
          <a-button type="text" class="action-btn">
            <BellOutlined />
          </a-button>
        </a-badge>

        <!-- 设置 -->
        <a-button type="text" class="action-btn">
          <SettingOutlined />
        </a-button>

        <!-- 用户菜单 -->
        <a-dropdown 
          v-model:open="userMenuVisible"
          placement="bottomRight"
          :trigger="['hover']"
        >
          <div class="user-info">
            <a-avatar :icon="UserOutlined" size="small" />
            <span class="username">{{ currentUser?.username || '管理员' }}</span>
          </div>
          
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile">
                <UserOutlined />
                个人资料
              </a-menu-item>
              <a-menu-item key="settings">
                <SettingOutlined />
                系统设置
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">
                <LogoutOutlined />
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
  </a-layout-header>
</template>

<style lang="scss" scoped>
.header {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 1000;
  height: 64px;
  line-height: 64px;
  padding-inline: 0 !important;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 18px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: #f5f5f5;
  }
}

.breadcrumb {
  margin: 0;
  
  :deep(.ant-breadcrumb-link) {
    color: #666;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  
  &:hover {
    background: #f5f5f5;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background: #f5f5f5;
  }
}

.username {
  font-size: 14px;
  color: #333;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// 响应式设计
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .username {
    display: none;
  }
}
</style>
