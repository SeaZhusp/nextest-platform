<script setup lang="ts">
defineProps<{
  skillLabel: string
  modelLabel: string
  temperatureTagText: string
  modelSelected: boolean
}>()

const emit = defineEmits<{
  'open-skill': []
  'open-model': []
  'open-temp': []
}>()
</script>

<template>
  <div class="composer-card__tags">
    <a-tag class="composer-tag" color="processing" @click="emit('open-skill')">
      {{ skillLabel }}
    </a-tag>
    <a-tag
      class="composer-tag"
      :color="modelSelected ? 'blue' : 'warning'"
      @click="emit('open-model')"
    >
      {{ modelLabel }}
    </a-tag>
    <a-tag class="composer-tag" @click="emit('open-temp')">
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
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;

  &:hover {
    opacity: 0.92;
  }
}
</style>
