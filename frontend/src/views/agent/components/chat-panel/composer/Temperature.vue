<script setup lang="ts">
const temperature = defineModel<number>({ default: 0.7 })
</script>

<template>
  <div class="composer-temp__body">
    <div class="composer-temp__title">温度 {{ temperature.toFixed(1) }}</div>
    <a-slider v-model:value="temperature" :min="0" :max="1" :step="0.1" />
    <div class="composer-temp__hint">越高越随机，越低越稳定</div>
  </div>
</template>

<style scoped lang="scss">
.composer-temp__body {
  width: 220px;
}

.composer-temp__title {
  font-size: 13px;
  margin-bottom: 8px;
  color: #262626;
}

.composer-temp__hint {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 4px;
}
</style>
