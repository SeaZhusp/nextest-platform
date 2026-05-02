<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta?.title as string) || '页面')
</script>

<template>
  <div class="hub-coming-soon">
    <h1 class="hub-coming-soon__title">{{ title }}</h1>
    <p class="hub-coming-soon__hint">功能建设中，敬请期待</p>
  </div>
</template>

<style lang="scss" scoped>
.hub-coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  padding: 24px;
  text-align: center;
}

.hub-coming-soon__title {
  margin: 0 0 12px;
  font-size: 20px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.hub-coming-soon__hint {
  margin: 0;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
