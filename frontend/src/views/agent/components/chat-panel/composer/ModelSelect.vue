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

function onPick(v: string | number) {
  const n = typeof v === 'number' ? v : Number(v)
  if (Number.isFinite(n)) emit('pick', n)
}
</script>

<template>
  <div class="composer-pop__body">
    <div class="composer-pop__title">选择模型</div>
    <a-select
      :value="selectedProfileId"
      class="composer-pop__select"
      :loading="profilesLoading"
      :disabled="profiles.length === 0 && !profilesLoading"
      option-label-prop="label"
      :dropdown-match-select-width="false"
      :dropdown-style="{ minWidth: '260px', maxWidth: '360px' }"
      popup-class-name="agent-chat-model-dropdown"
      :placeholder="profiles.length === 0 ? '暂无模型配置' : '请选择模型'"
      @update:value="onPick"
    >
      <template #optionLabel="opt">
        <span v-if="opt" class="composer-model-opt__selection">
          <LlmProviderIcon
            v-if="opt.provider"
            :meta="providerMeta(opt.provider)"
            :size="18"
          />
          <span class="composer-model-opt__selection-text">{{ opt.label }}</span>
        </span>
      </template>
      <a-select-opt-group v-if="profiles.length" label="我的配置">
        <a-select-option
          v-for="p in profiles"
          :key="p.id"
          :value="p.id"
          :label="p.display_name"
          :provider="p.provider"
        >
          <div class="composer-model-opt__row">
            <LlmProviderIcon :meta="providerMeta(p.provider)" :size="18" />
            <span class="composer-model-opt__name">{{ p.display_name }}</span>
            <a-tag color="success" class="composer-model-opt__tag">我的</a-tag>
          </div>
        </a-select-option>
      </a-select-opt-group>
    </a-select>
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

.composer-model-opt__selection {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
}

.composer-model-opt__selection-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-model-opt__row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.composer-model-opt__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.composer-model-opt__tag {
  margin: 0 !important;
  flex-shrink: 0;
  font-size: 11px;
  line-height: 18px;
}
</style>
