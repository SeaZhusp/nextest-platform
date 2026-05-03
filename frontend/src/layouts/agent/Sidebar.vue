<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { LogoutOutlined, CloudOutlined, DownOutlined } from '@ant-design/icons-vue'
import type { AuthUserInfo } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { AGENT_SIDEBAR_NEW_SESSION } from '@/constants/agentSidebarBridge'
import History from './components/History.vue'
import Logo from '../components/Logo.vue'
import Menu from './components/Menu.vue'
import NewSession from './components/NewSession.vue'

interface Props {
  collapsed: boolean
  currentUser: AuthUserInfo | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggleCollapsed: []
}>()

const router = useRouter()
const authStore = useAuthStore()

function emitToggleCollapsed() {
  emit('toggleCollapsed')
}

const displayName = computed(() => {
  const u = props.currentUser
  if (!u) return '管理员'
  const nick = u.nickname?.trim()
  if (nick) return nick
  return u.username || '管理员'
})

const avatarLetter = computed(() => {
  const u = props.currentUser
  if (!u) return '管'
  const source = (u.nickname?.trim() || u.username || '').trim()
  if (!source) return '?'
  const first = [...source][0]
  return first || '?'
})

const userMenuVisible = ref(false)

async function handleLogout() {
  userMenuVisible.value = false
  await authStore.logout()
  void router.push('/login')
}

function goLlmProfiles() {
  userMenuVisible.value = false
  void router.push('/settings/llm-profiles')
}

async function afterNavigateDispatch(fn: () => void) {
  await nextTick()
  requestAnimationFrame(() => {
    fn()
  })
}

async function goNewSession() {
  const route = router.currentRoute.value
  if (route.path !== '/agent') {
    await router.push('/agent')
  }
  await afterNavigateDispatch(() => {
    window.dispatchEvent(new CustomEvent(AGENT_SIDEBAR_NEW_SESSION))
  })
}
</script>

<template>
  <a-layout-sider
    :collapsed="false"
    :width="260"
    class="sidebar"
    :class="{ 'sidebar--hidden': collapsed }"
    :style="{
      position: 'fixed',
      left: 0,
      top: 0,
      height: '100vh',
      zIndex: 999,
    }"
  >
    <div class="sidebar-inner">
      <Logo @toggle-collapsed="emitToggleCollapsed" />

      <NewSession @new-session="goNewSession" />

      <Menu />

      <History />

      <div class="sidebar-footer">
        <a-dropdown
          v-model:open="userMenuVisible"
          placement="topLeft"
          :trigger="['hover']"
        >
          <div class="sidebar-user-trigger">
            <a-avatar :size="30" class="sidebar-user-avatar">{{ avatarLetter }}</a-avatar>
            <span class="sidebar-user-name">{{ displayName }}</span>
            <DownOutlined class="sidebar-user-caret" />
          </div>

          <template #overlay>
            <a-menu>
              <a-menu-item key="llm-profiles" @click="goLlmProfiles">
                <CloudOutlined />
                基本信息
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
  </a-layout-sider>
</template>

<style lang="scss" scoped>
.sidebar {
  background: #fff;
  border-right: 1px solid #f0f0f0;
  overflow: hidden;
  transition: transform 0.2s ease;

  :deep(.ant-layout-sider-children) {
    height: 100%;
    overflow: hidden;
    display: block;
  }

  &--hidden {
    transform: translateX(-100%);
    pointer-events: none;
    border-right: none;
  }
}

.sidebar-inner {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
}

.sidebar-footer {
  padding: 10px 8px;
  border-top: 1px solid #f0f0f0;
  background: #fff;
}

.sidebar-user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  line-height: normal;
  transition: background-color 0.2s;

  &:hover {
    background: #f5f5f5;
  }

}

.sidebar-user-avatar {
  flex-shrink: 0;
  background: #bfbfbf !important;
  color: #fff !important;
  font-size: 13px !important;
  font-weight: 300;
}

.sidebar-user-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-user-caret {
  flex-shrink: 0;
  font-size: 10px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
