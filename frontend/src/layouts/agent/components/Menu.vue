<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { FolderOutlined, CloudOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()

/** 侧栏固定菜单：路径与 router 中页面一致 */
const menuItems = [
  { key: '/agent', label: '我的项目', icon: FolderOutlined },
  { key: '/llm', label: '模型配置', icon: CloudOutlined },
] as const

const selectedKeys = computed(() => {
  const am = route.meta.activeMenu
  if (typeof am === 'string' && am.length > 0) {
    const hit = menuItems.find((item) => item.key === am)
    if (hit) return [hit.key]
  }
  const p = route.path
  for (const item of menuItems) {
    if (p === item.key || p.startsWith(`${item.key}/`)) return [item.key]
  }
  return []
})

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
      :selected-keys="selectedKeys"
      mode="inline"
      class="sidebar-menu"
      @click="onMenuClick"
    >
      <div
        v-for="item in menuItems"
        :key="'leaf-' + item.key"
        class="sidebar-menu__entry"
      >
        <a-menu-item :key="item.key">
          <component :is="item.icon" class="sidebar-menu__icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </div>
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
}
</style>
