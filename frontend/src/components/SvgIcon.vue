<script setup lang="ts">
import { computed } from 'vue'

/** 仅允许文件名安全字符，对应 `src/assets/icons/{name}.svg` */
const ICON_NAME = /^[a-zA-Z0-9_-]+$/

const rawByRelPath = import.meta.glob<string>('@/assets/icons/*.svg', {
  eager: true,
  query: '?raw',
  import: 'default',
})

const rawByName: Record<string, string> = {}
for (const path of Object.keys(rawByRelPath)) {
  const m = path.match(/\/([^/]+)\.svg$/)
  if (m) rawByName[m[1]] = rawByRelPath[path]
}

const props = withDefaults(
  defineProps<{
    /** 不含 `.svg`，映射到 `@/assets/icons/{name}.svg` */
    name: string
    /** 边长（px） */
    size?: number
  }>(),
  { size: 18 }
)

const raw = computed(() => {
  if (!ICON_NAME.test(props.name)) {
    if (import.meta.env.DEV) {
      console.warn(`[SvgIcon] invalid name: ${props.name}`)
    }
    return ''
  }
  const svg = rawByName[props.name]
  if (!svg && import.meta.env.DEV) {
    console.warn(`[SvgIcon] missing icon: @/assets/icons/${props.name}.svg`)
  }
  return svg ?? ''
})

const sizePx = computed(() => `${props.size}px`)
</script>

<template>
  <span
    v-if="raw"
    class="svg-icon"
    aria-hidden="true"
    :style="{ width: sizePx, height: sizePx, color: 'inherit' }"
    v-html="raw"
  />
</template>

<style scoped>
.svg-icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
}

.svg-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
