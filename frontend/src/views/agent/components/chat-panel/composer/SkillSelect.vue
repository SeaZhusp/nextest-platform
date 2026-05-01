<script setup lang="ts">
import SvgIcon from '@/components/SvgIcon.vue'

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
  <div class="composer-picker">
    <a-spin :spinning="loading">
      <div v-if="!loading && !options.length" class="composer-picker__empty">暂无技能</div>
      <div v-else class="composer-picker__list" role="listbox">
        <button
          v-for="o in options"
          :key="o.value"
          type="button"
          class="composer-picker__row"
          :class="{ 'composer-picker__row--active': o.value === selectedSkillId }"
          role="option"
          :aria-selected="o.value === selectedSkillId"
          @click="emit('pick', o.value)"
        >
          <span class="composer-picker__icon" aria-hidden="true">
            <SvgIcon name="skill" :size="18" />
          </span>
          <span class="composer-picker__name">{{ o.label }}</span>
        </button>
      </div>
    </a-spin>
  </div>
</template>

<style scoped lang="scss">
.composer-picker {
  width: 280px;
  max-width: min(280px, 85vw);
}

.composer-picker__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 280px;
  overflow-y: auto;
  margin: 0;
  padding: 2px 0;
}

.composer-picker__row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  margin: 0;
  padding: 8px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #262626;
  font-size: 14px;
  line-height: 1.4;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s ease;

  &:hover {
    background: #e6f4ff;
  }

  &--active {
    background: #e6f4ff;
    color: #0958d9;
  }
}

.composer-picker__icon {
  flex-shrink: 0;
  display: inline-flex;
  color: #1677ff;
  opacity: 0.95;
}

.composer-picker__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-picker__empty {
  padding: 12px 10px;
  font-size: 13px;
  color: #8c8c8c;
  text-align: center;
}
</style>
