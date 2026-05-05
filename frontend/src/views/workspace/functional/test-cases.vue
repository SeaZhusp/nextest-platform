<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectId = computed(() => String(route.params.projectId || ''))
</script>

<template>
  <div class="cases-shell">
    <div class="cases-shell__card">
      <h2 class="cases-shell__title">测试用例</h2>
      <p class="cases-shell__desc">
        项目 <strong>#{{ projectId }}</strong>：左侧模块树 + 右侧用例列表将在此接入；当前为布局占位。
      </p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.cases-shell {
  max-width: 1200px;
  margin: 0 auto;
}

.cases-shell__card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.cases-shell__title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.cases-shell__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.55);
}
</style>
