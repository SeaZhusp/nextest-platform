import { ref, watch } from 'vue'

/** 技能 / 模型 / 温度三个 Popover 互斥（由工具栏图标点击打开） */
export function useComposerPopovers() {
  const skillPopoverOpen = ref(false)
  const modelPopoverOpen = ref(false)
  const tempPopoverOpen = ref(false)

  watch(skillPopoverOpen, (open) => {
    if (open) {
      modelPopoverOpen.value = false
      tempPopoverOpen.value = false
    }
  })

  watch(modelPopoverOpen, (open) => {
    if (open) {
      skillPopoverOpen.value = false
      tempPopoverOpen.value = false
    }
  })

  watch(tempPopoverOpen, (open) => {
    if (open) {
      skillPopoverOpen.value = false
      modelPopoverOpen.value = false
    }
  })

  return {
    skillPopoverOpen,
    modelPopoverOpen,
    tempPopoverOpen
  }
}
