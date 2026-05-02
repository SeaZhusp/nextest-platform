<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  DashboardOutlined,
  RobotOutlined,
  SettingOutlined,
  UserOutlined,
  FileTextOutlined,
  DesktopOutlined,
  ApiOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'

export interface MenuItem {
  key: string
  label: string
  icon?: Component
  children?: MenuItem[]
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

function canSeeRouteMeta(meta: Record<string, unknown> | undefined): boolean {
  const role = meta?.role as string | undefined
  if (!role) return true
  return authStore.currentUser?.user_type === role
}

const iconMap: Record<string, Component> = {
  DashboardOutlined,
  RobotOutlined,
  SettingOutlined,
  UserOutlined,
  FileTextOutlined,
  DesktopOutlined,
  ApiOutlined,
  ThunderboltOutlined,
}

function resolveAbsPath(parentAbs: string, segment: string): string {
  const s = segment || ''
  if (parentAbs === '/') {
    if (s === '' || s === '/') return '/'
    return s.startsWith('/') ? s : `/${s}`
  }
  const base = parentAbs.replace(/\/$/, '')
  const child = s.replace(/^\//, '')
  return `${base}/${child}`
}

function buildMenuTree(records: RouteRecordRaw[] | undefined, parentAbs: string): MenuItem[] {
  if (!records?.length) return []
  const out: MenuItem[] = []

  for (const r of records) {
    const meta = r.meta as Record<string, unknown> | undefined
    if (meta?.showInMenu === false) continue
    if (!canSeeRouteMeta(meta)) continue

    const segment = typeof r.path === 'string' ? r.path : ''
    const absPath = resolveAbsPath(parentAbs, segment)
    const childRecords = r.children ?? []
    const childItems = buildMenuTree(childRecords, absPath)

    const label = String(meta?.title ?? String(r.name ?? absPath))
    const iconName = meta?.icon as string | undefined
    const icon = iconName ? iconMap[iconName] : undefined

    if (childItems.length > 0) {
      out.push({ key: absPath, label, icon, children: childItems })
      continue
    }

    if (childRecords.length > 0) continue

    const hasLeaf =
      !!r.component || !!(r.components && r.components.default) || r.redirect !== undefined
    if (!hasLeaf) continue

    out.push({ key: absPath, label, icon })
  }

  return out
}

const menuItems = computed<MenuItem[]>(() => {
  const options = router.options.routes
  const layoutRoute = options.find((r) => r.path === '/')
  const children = (layoutRoute?.children ?? []) as RouteRecordRaw[]
  return buildMenuTree(children, '/')
})

const selectedKeys = computed(() => {
  const am = route.meta.activeMenu
  const path =
    typeof am === 'string' && am.length > 0
      ? am
      : route.path === '' || route.path === '/'
        ? '/'
        : route.path
  return [path]
})

function computeOpenKeys(items: MenuItem[], currentPath: string): string[] {
  const keys: string[] = []
  for (const item of items) {
    if (!item.children?.length) continue
    const childHit = item.children.some(
      (c) => currentPath === c.key || currentPath.startsWith(`${c.key}/`)
    )
    const prefixHit =
      item.key !== '/' &&
      (currentPath === item.key || currentPath.startsWith(`${item.key}/`))
    if (childHit || prefixHit) keys.push(item.key)
  }
  return keys
}

const openKeys = ref<string[]>([])

function syncOpenKeys() {
  openKeys.value = computeOpenKeys(menuItems.value, route.path)
}

watch(
  () => route.path,
  () => {
    syncOpenKeys()
  },
  { immediate: true }
)

watch(menuItems, () => syncOpenKeys(), { deep: true })

function onMenuClick(info: { key: string }) {
  const key = info.key
  if (!key) return
  if (router.currentRoute.value.path !== key) {
    void router.push(key)
  }
}
</script>

<template>
  <nav class="sidebar-menu-wrap" aria-label="主导航">
    <a-menu
      v-model:open-keys="openKeys"
      :selected-keys="selectedKeys"
      mode="inline"
      class="sidebar-menu"
      @click="onMenuClick"
    >
      <!-- 外层用不同 key 满足 Vue v-if/else 规则；菜单项 key 仍为路由 path，勿加 leaf- 前缀 -->
      <template v-for="item in menuItems" :key="item.key">
        <div v-if="item.children?.length" :key="'branch-' + item.key" class="sidebar-menu__entry">
          <a-sub-menu :key="item.key">
            <template #title>
              <component :is="item.icon" v-if="item.icon" class="sidebar-menu__icon" />
              <span>{{ item.label }}</span>
            </template>
            <a-menu-item v-for="child in item.children" :key="child.key">
              <component :is="child.icon" v-if="child.icon" class="sidebar-menu__icon" />
              <span>{{ child.label }}</span>
            </a-menu-item>
          </a-sub-menu>
        </div>
        <div v-else :key="'leaf-' + item.key" class="sidebar-menu__entry">
          <a-menu-item :key="item.key">
            <component :is="item.icon" v-if="item.icon" class="sidebar-menu__icon" />
            <span>{{ item.label }}</span>
          </a-menu-item>
        </div>
      </template>
    </a-menu>
  </nav>
</template>

<style lang="scss" scoped>
.sidebar-menu-wrap {
  flex-shrink: 0;
  min-height: 0;
  padding: 4px 0 8px;
}

.sidebar-menu__entry {
  display: contents;
}

.sidebar-menu__icon {
  font-size: 16px;
}

.sidebar-menu {
  border-inline-end: none;
  background: transparent;

  :deep(.ant-menu-item) {
    color: rgba(0, 0, 0, 0.85);
    margin: 4px 8px;
    height: 40px;
    line-height: 40px;
    padding-left: 16px !important;
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
      padding-left: 16px !important;
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
      padding-left: 40px !important;
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
</style>
