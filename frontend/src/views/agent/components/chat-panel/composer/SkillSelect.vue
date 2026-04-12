<script setup lang="ts">
defineProps<{
  selectedSkillId: string
  options: { label: string; value: string }[]
  loading: boolean
}>()

const emit = defineEmits<{
  pick: [skillId: string]
}>()
</script>

<template>
  <div class="composer-pop__body">
    <div class="composer-pop__title">选择技能</div>
    <a-select
      :value="selectedSkillId"
      show-search
      :options="options"
      option-filter-prop="label"
      class="composer-pop__select"
      :loading="loading"
      :dropdown-match-select-width="false"
      :dropdown-style="{ minWidth: '260px', maxWidth: '360px' }"
      popup-class-name="agent-chat-skill-dropdown"
      placeholder="请选择技能"
      @update:value="(v: string | number) => emit('pick', String(v))"
    />
  </div>
</template>

<style scoped lang="scss">
.composer-pop__body {
  min-width: 240px;
}

.composer-pop__title {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.composer-pop__select {
  width: 280px;
  max-width: min(280px, 85vw);
}
</style>
