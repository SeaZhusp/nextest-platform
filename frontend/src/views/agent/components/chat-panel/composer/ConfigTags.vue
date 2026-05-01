<script setup lang="ts">
defineProps<{
  skillLabel: string
  modelLabel: string
  temperatureTagText: string
  modelSelected: boolean
}>()
</script>

<template>
  <div class="composer-card__tags">
    <a-tag class="composer-tag" color="processing">
      {{ skillLabel }}
    </a-tag>
    <a-tag class="composer-tag" :color="modelSelected ? 'blue' : 'warning'">
      {{ modelLabel }}
    </a-tag>
    <a-tag class="composer-tag">
      {{ temperatureTagText }}
    </a-tag>
  </div>
</template>

<style scoped lang="scss">
.composer-card__tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 0 12px 10px 12px;
}

.composer-tag {
  margin: 0 !important;
  max-width: 100%;
  cursor: default;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
