<script setup lang="ts">
import LlmProviderIcon from '@/components/LlmProviderIcon.vue'
import { providerMeta } from '@/config/llmProviders'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'

defineProps<{
  selectedProfileId: number | null
  profiles: UserLlmProfileOut[]
  profilesLoading: boolean
}>()

const emit = defineEmits<{
  pick: [profileId: number]
}>()
</script>

<template>
  <div class="composer-picker">
    <a-spin :spinning="profilesLoading">
      <div v-if="!profilesLoading && !profiles.length" class="composer-picker__empty">
        暂无模型配置
      </div>
      <div v-else class="composer-picker__list" role="listbox">
        <button
          v-for="p in profiles"
          :key="p.id"
          type="button"
          class="composer-picker__row"
          :class="{ 'composer-picker__row--active': p.id === selectedProfileId }"
          role="option"
          :aria-selected="p.id === selectedProfileId"
          @click="emit('pick', p.id)"
        >
          <span class="composer-picker__icon" aria-hidden="true">
            <LlmProviderIcon :meta="providerMeta(p.provider)" :size="18" />
          </span>
          <span class="composer-picker__name">{{ p.display_name }}</span>
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
