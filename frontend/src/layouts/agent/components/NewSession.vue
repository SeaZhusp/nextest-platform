<script setup lang="ts">
import { PlusOutlined } from '@ant-design/icons-vue'

const emit = defineEmits<{
  'new-session': []
}>()
</script>

<template>
  <div class="new-session">
    <div class="new-session__primary">
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
</style>
