<script setup lang="ts">
const model = defineModel<string>({ default: '' })

const emit = defineEmits<{
  send: []
}>()
</script>

<template>
  <a-textarea
    v-model:value="model"
    :bordered="false"
    :rows="4"
    :auto-size="{ minRows: 3, maxRows: 8 }"
    placeholder="描述您的需求，例如：帮我生成一个登录功能的测试用例…"
    class="composer-textarea"
    @pressEnter.exact.prevent="emit('send')"
  />
</template>

<style scoped lang="scss">
.composer-textarea {
  padding: 14px 16px 8px;
  font-size: 14px;
  line-height: 1.55;
  resize: none;

  :deep(.ant-input) {
    padding: 0;
    box-shadow: none !important;
  }
}
</style>
