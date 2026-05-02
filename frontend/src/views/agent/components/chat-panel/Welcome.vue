<script setup lang="ts">
const emit = defineEmits<{
  'apply-prompt': [text: string]
}>()

const suggestions = [
  '请根据需求描述生成登录与注册的测试用例',
  '列出支付回调超时场景的验收要点',
  '帮我梳理订单取消流程的接口测试场景',
  '如何用等价类划分搜索框输入校验？',
  '生成一份简易的性能测试关注点清单',
  '请推荐几款适合接口契约测试的工具链',
  '如何判断缺陷优先级是否合理？',
  '输出敏捷迭代中的冒烟测试清单模板',
  '请解释边界值分析法并给一个示例',
]

function onChip(text: string) {
  emit('apply-prompt', text)
}
</script>

<template>
  <div class="agent-chat__welcome">
    <div class="agent-chat__welcome-inner">
      <h1 class="agent-chat__greeting">有什么我能帮你的吗？</h1>
      <div class="agent-chat__chips" role="list">
        <button
          v-for="(text, i) in suggestions"
          :key="i"
          type="button"
          class="agent-chat__chip"
          role="listitem"
          @click="onChip(text)"
        >
          {{ text }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-chat__welcome {
  flex: 1;
  min-height: 0;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.agent-chat__welcome-inner {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  text-align: center;
}

.agent-chat__greeting {
  margin: 0 0 28px;
  font-size: 28px;
  font-weight: 600;
  color: #141414;
  letter-spacing: 0.02em;
  line-height: 1.35;
}

.agent-chat__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.agent-chat__chip {
  appearance: none;
  margin: 0;
  padding: 10px 16px;
  max-width: 100%;
  text-align: left;
  font-size: 13px;
  line-height: 1.45;
  color: #434343;
  background: #f0f0f0;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;

  &:hover {
    background: #e6e6e6;
    color: #141414;
  }

  &:active {
    background: #dedede;
  }
}

@media (max-width: 768px) {
  .agent-chat__greeting {
    font-size: 22px;
    margin-bottom: 20px;
  }
}
</style>
