<script setup lang="ts">
import { ref } from 'vue'
import { AppstoreOutlined, MenuFoldOutlined } from '@ant-design/icons-vue'

withDefaults(
  defineProps<{
    /** 是否显示侧栏收起按钮（管理后台顶栏已有折叠入口，一般为 false） */
    showCollapseTrigger?: boolean
  }>(),
  {
    showCollapseTrigger: false,
  },
)

const emit = defineEmits<{
  toggleCollapsed: []
}>()

const LOGO_SRC = '/logo.jpg'
const logoFailed = ref(false)

function onLogoError() {
  logoFailed.value = true
}
</script>

<template>
  <div class="logo">
    <div class="sidebar-logo-row">
      <div class="logo-content">
        <img
          v-if="!logoFailed"
          key="sidebar-logo-img"
          :src="LOGO_SRC"
          alt="NexTest"
          class="logo-img"
          @error="onLogoError"
        />
        <AppstoreOutlined
          v-else
          key="sidebar-logo-fallback"
          class="logo-fallback"
          aria-hidden="true"
        />
        <div class="logo-text">
          <span class="logo-brand">NexTest</span>
          <span class="logo-tagline">下一代测试平台</span>
        </div>
      </div>
      <a-button
        v-if="showCollapseTrigger"
        type="text"
        class="sidebar-fold-btn"
        aria-label="收起侧边栏"
        title="收起侧边栏"
        @click="emit('toggleCollapsed')"
      >
        <MenuFoldOutlined />
      </a-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.logo {
  flex-shrink: 0;
}

.sidebar-logo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 56px;
  padding: 8px 10px;
  background: #fff;
}

.sidebar-fold-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  font-size: 16px;

  &:hover {
    background: #f5f5f5;
  }
}

.logo-content {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  padding: 0 4px;
}

.logo-img {
  height: 44px;
  width: auto;
  max-width: 44px;
  object-fit: contain;
  flex-shrink: 0;
  border-radius: 6px;
}

.logo-fallback {
  flex-shrink: 0;
  font-size: 28px;
  color: #1890ff;
}

.logo-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  min-width: 0;
}

.logo-brand {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.15;
  color: rgba(0, 0, 0, 0.88);
  letter-spacing: 0.02em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logo-tagline {
  font-size: 12px;
  line-height: 1.2;
  color: rgba(0, 0, 0, 0.45);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
