<script setup lang="ts">
import {
  RobotOutlined,
  CommentOutlined,
  ThunderboltOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
</script>

<template>
  <div class="agent-chat__welcome">
    <div class="agent-chat__welcome-inner">
      <div class="agent-chat__welcome-icon" aria-hidden="true">
        <RobotOutlined />
      </div>
      <ul class="agent-chat__features">
        <li><CommentOutlined /> 智能对话</li>
        <li><ThunderboltOutlined /> 快速响应</li>
        <li><UnorderedListOutlined /> 结果结构化输出</li>
      </ul>
      <p class="agent-chat__hint">
        选择技能与模型后输入你的需求，即可开始对话并在左侧查看输出结果。你也可以先发一条简单问题来快速体验。
      </p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.agent-chat__welcome {
  flex: 1;
  min-height: 0;
  padding: 24px 16px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bfbfbf;
}

.agent-chat__welcome-inner {
  width: min(460px, 100%);
  text-align: center;
}

.agent-chat__welcome-icon {
  margin-bottom: 20px;
  font-size: 48px;
  line-height: 1;
  color: #8c8c8c;
}

.agent-chat__features {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.8;
  text-align: center;
  color: #8c8c8c;
  max-width: 260px;
  margin-left: auto;
  margin-right: auto;
}

.agent-chat__features li {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.agent-chat__hint {
  margin: 18px auto 0;
  max-width: 380px;
  font-size: 13px;
  line-height: 1.65;
  color: #bfbfbf;
}
</style>
