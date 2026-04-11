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
  DownOutlined,
} from '@ant-design/icons-vue'
import type { AuthUserInfo } from '@/api/auth'

interface Props {
  collapsed: boolean
  isLoggedIn: boolean
  currentUser: AuthUserInfo | null
}

const props = defineProps<Props>()

const route = useRoute()

/** 右侧展示：优先昵称，否则用户名 */
const displayName = computed(() => {
  const u = props.currentUser
  if (!u) return '管理员'
  const nick = u.nickname?.trim()
  if (nick) return nick
  return u.username || '管理员'
})

/** 头像文字：优先昵称首字，否则用户名首字 */
const avatarLetter = computed(() => {
  const u = props.currentUser
  if (!u) return '管'
  const source = (u.nickname?.trim() || u.username || '').trim()
  if (!source) return '?'
  const first = [...source][0]
  return first || '?'
})

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
            <a-avatar :size="30" class="user-avatar">{{ avatarLetter }}</a-avatar>
            <span class="user-display">{{ displayName }}</span>
            <DownOutlined class="user-caret" />
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
  gap: 10px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s, box-shadow 0.2s;
  /* 避免继承 .header 的 line-height: 64px，否则头像内文字会偏上/偏下 */
  line-height: normal;
  
  &:hover {
    background: #f5f5f5;
    /* 略加大纵向扩散，hover 时更有「浮起」感 */
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  }
}

/* 浅灰底 + 白字。不要改 Avatar 内联的 line-height / transform（含 translateX(-50%)），否则单字会偏位 */
.user-avatar {
  flex-shrink: 0;
  background: #bfbfbf !important;
  color: #fff !important;
  /* 覆盖 Avatar 数字 size 时内联的 18px，避免小圆里字偏大 */
  font-size: 13px !important;
  font-weight: 300;
}

.user-display {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.88);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-caret {
  flex-shrink: 0;
  font-size: 10px;
  color: rgba(0, 0, 0, 0.45);
}

// 响应式设计
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .user-display,
  .user-caret {
    display: none;
  }
}
</style>
