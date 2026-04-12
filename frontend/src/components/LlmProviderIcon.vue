<script setup lang="ts">
import type { LlmProviderItem } from '@/config/llmProviders'

withDefaults(
  defineProps<{
    meta: LlmProviderItem
    /** 卡片大图标用 22，下拉里用 20 */
    size?: number
  }>(),
  { size: 20 }
)
</script>

<template>
  <img
    v-if="meta.logo"
    class="llm-provider-icon-img"
    :src="meta.logo"
    :width="size"
    :height="size"
    alt=""
  />
  <component
    :is="meta.fallbackIcon"
    v-else
    class="llm-provider-icon-fallback"
    :style="{ color: meta.color, fontSize: `${size}px` }"
  />
</template>

<style scoped>
.llm-provider-icon-img {
  display: block;
  object-fit: contain;
  flex-shrink: 0;
  border-radius: 6px;
}

.llm-provider-icon-fallback {
  display: block;
  flex-shrink: 0;
}
</style>
