import { ref, watch } from 'vue'

/** 技能 / 模型 / 温度三个 Popover 互斥，并提供从 tag 打开的入口 */
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

  function openSkillPopover() {
    modelPopoverOpen.value = false
    tempPopoverOpen.value = false
    skillPopoverOpen.value = true
  }

  function openModelPopover() {
    skillPopoverOpen.value = false
    tempPopoverOpen.value = false
    modelPopoverOpen.value = true
  }

  function openTempPopover() {
    skillPopoverOpen.value = false
    modelPopoverOpen.value = false
    tempPopoverOpen.value = true
  }

  return {
    skillPopoverOpen,
    modelPopoverOpen,
    tempPopoverOpen,
    openSkillPopover,
    openModelPopover,
    openTempPopover
  }
}
