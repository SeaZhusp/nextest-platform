<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CloseOutlined,
  ReloadOutlined,
  LeftOutlined,
  RightOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

export interface TabItem {
  key: string
  title: string
  path: string
  closable?: boolean
  icon?: string
}

interface Props {
  tabs: TabItem[]
  activeKey: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  updateActiveKey: [key: string]
  closeTab: [key: string]
  closeOtherTabs: [key: string]
  closeAllTabs: []
  refreshTab: [key: string]
}>()

const router = useRouter()
const route = useRoute()

// 标签页滚动位置
const scrollPosition = ref(0)
const tabContainerRef = ref<HTMLElement>()

// 计算可见的标签页
const visibleTabs = computed(() => {
  const containerWidth = tabContainerRef.value?.clientWidth || 0
  const tabWidth = 120 // 每个标签页的宽度
  const maxVisible = Math.floor(containerWidth / tabWidth)
  
  if (props.tabs.length <= maxVisible) {
    return props.tabs
  }
  
  const start = scrollPosition.value
  const end = Math.min(start + maxVisible, props.tabs.length)
  return props.tabs.slice(start, end)
})

// 是否可以向左滚动
const canScrollLeft = computed(() => scrollPosition.value > 0)

// 是否可以向右滚动
const canScrollRight = computed(() => {
  const containerWidth = tabContainerRef.value?.clientWidth || 0
  const tabWidth = 120
  const maxVisible = Math.floor(containerWidth / tabWidth)
  return scrollPosition.value + maxVisible < props.tabs.length
})

// 切换标签页
function handleTabClick(tab: TabItem) {
  emit('updateActiveKey', tab.key)
  router.push(tab.path)
}

// 关闭标签页
function handleCloseTab(tab: TabItem, event: Event) {
  event.stopPropagation()
  emit('closeTab', tab.key)
}

// 刷新标签页
function handleRefreshTab(tab: TabItem, event: Event) {
  event.stopPropagation()
  emit('refreshTab', tab.key)
}

// 关闭其他标签页
function handleCloseOtherTabs(tab: TabItem, event: Event) {
  event.stopPropagation()
  emit('closeOtherTabs', tab.key)
}

// 关闭所有标签页
function handleCloseAllTabs(event: Event) {
  event.stopPropagation()
  emit('closeAllTabs')
}

// 向左滚动
function scrollLeft() {
  if (canScrollLeft.value) {
    scrollPosition.value = Math.max(0, scrollPosition.value - 1)
  }
}

// 向右滚动
function scrollRight() {
  if (canScrollRight.value) {
    scrollPosition.value = Math.min(
      props.tabs.length - Math.floor((tabContainerRef.value?.clientWidth || 0) / 120),
      scrollPosition.value + 1
    )
  }
}

// 监听路由变化，确保当前标签页可见
watch(() => route.path, (newPath) => {
  const currentTab = props.tabs.find(tab => tab.path === newPath)
  if (currentTab) {
    const tabIndex = props.tabs.findIndex(tab => tab.key === currentTab.key)
    const containerWidth = tabContainerRef.value?.clientWidth || 0
    const tabWidth = 120
    const maxVisible = Math.floor(containerWidth / tabWidth)
    
    if (tabIndex < scrollPosition.value) {
      scrollPosition.value = tabIndex
    } else if (tabIndex >= scrollPosition.value + maxVisible) {
      scrollPosition.value = tabIndex - maxVisible + 1
    }
  }
})
</script>

<template>
  <div class="tab-view">
    <!-- 标签页容器 -->
    <div class="tab-container" ref="tabContainerRef">
      <!-- 滚动按钮 -->
      <div v-if="props.tabs.length > 0" class="scroll-buttons">
        <a-button 
          type="text" 
          size="small" 
          :disabled="!canScrollLeft"
          @click="scrollLeft"
          class="scroll-btn"
        >
          <LeftOutlined />
        </a-button>
        <a-button 
          type="text" 
          size="small" 
          :disabled="!canScrollRight"
          @click="scrollRight"
          class="scroll-btn"
        >
          <RightOutlined />
        </a-button>
      </div>

      <!-- 标签页列表 -->
      <div class="tab-list">
        <div
          v-for="tab in visibleTabs"
          :key="tab.key"
          :class="['tab-item', { active: props.activeKey === tab.key }]"
          @click="handleTabClick(tab)"
        >
          <div class="tab-content">
            <span class="tab-title">{{ tab.title }}</span>
            <div class="tab-actions">
              <a-button
                v-if="tab.closable !== false"
                type="text"
                size="small"
                @click="handleCloseTab(tab, $event)"
                class="tab-close-btn"
              >
                <CloseOutlined />
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页操作菜单 -->
    <div v-if="props.tabs.length > 0" class="tab-actions">
      <a-dropdown>
        <a-button type="text" size="small">
          操作
          <DownOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item @click="handleRefreshTab(props.tabs.find(t => t.key === props.activeKey)!, $event)">
              <ReloadOutlined />
              刷新当前页
            </a-menu-item>
            <a-menu-item 
              v-if="props.tabs.length > 1"
              @click="handleCloseOtherTabs(props.tabs.find(t => t.key === props.activeKey)!, $event)"
            >
              关闭其他
            </a-menu-item>
            <a-menu-item @click="handleCloseAllTabs($event)">
              关闭所有
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.tab-view {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  height: 40px;
  padding: 0 16px;
}

.tab-container {
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.scroll-buttons {
  display: flex;
  gap: 4px;
  margin-right: 8px;
}

.scroll-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  
  &:disabled {
    opacity: 0.3;
  }
}

.tab-list {
  display: flex;
  gap: 2px;
  overflow: hidden;
}

.tab-item {
  min-width: 120px;
  max-width: 200px;
  height: 32px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px 4px 0 0;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  
  &:hover {
    background: #e6f7ff;
    border-color: #91d5ff;
  }
  
  &.active {
    background: #fff;
    border-color: #1890ff;
    border-bottom-color: #fff;
    z-index: 1;
    
    .tab-title {
      color: #1890ff;
      font-weight: 500;
    }
  }
}

.tab-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 12px;
}

.tab-title {
  flex: 1;
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.tab-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tab-close-btn {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 10px;
  opacity: 0.6;
  
  &:hover {
    opacity: 1;
    background: #ff4d4f;
    color: #fff;
  }
}

.tab-actions {
  margin-left: 8px;
}

// 响应式设计
@media (max-width: 768px) {
  .tab-view {
    padding: 0 8px;
  }
  
  .tab-item {
    min-width: 100px;
  }
  
  .tab-title {
    font-size: 11px;
  }
}
</style>
