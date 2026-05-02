<script setup lang="ts">
import { PlusOutlined } from '@ant-design/icons-vue'

defineProps<{
  collapsed: boolean
}>()

const emit = defineEmits<{
  'new-session': []
}>()
</script>

<template>
  <div class="new-session">
    <div v-if="!collapsed" class="new-session__primary">
      <button
        type="button"
        class="new-session__btn"
        aria-label="新建会话"
        @click="emit('new-session')"
      >
        <PlusOutlined class="new-session__btn-icon" aria-hidden="true" />
        <span>新建会话</span>
      </button>
    </div>

    <div v-else class="new-session__collapsed">
      <a-button
        type="text"
        class="new-session__icon-btn"
        title="新建会话"
        aria-label="新建会话"
        @click="emit('new-session')"
      >
        <PlusOutlined />
      </a-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.new-session {
  flex-shrink: 0;
}

.new-session__primary {
  padding: 0 10px 10px;
}

.new-session__btn {
  box-sizing: border-box;
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0;
  padding: 10px 12px;
  border: 1px solid rgba(24, 144, 255, 0.45);
  border-radius: 8px;
  background: rgba(24, 144, 255, 0.06);
  color: #1890ff;
  font-size: 14px;
  line-height: 1.2;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;

  &:hover {
    background: rgba(24, 144, 255, 0.1);
    border-color: rgba(24, 144, 255, 0.65);
  }

  &:active {
    background: rgba(24, 144, 255, 0.14);
  }
}

.new-session__btn-icon {
  font-size: 16px;
}

.new-session__collapsed {
  display: flex;
  justify-content: center;
  padding: 4px 0 8px;
  border-bottom: 1px solid #f0f0f0;
}

.new-session__icon-btn {
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
</style>
