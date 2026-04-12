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
    <RobotOutlined class="agent-chat__welcome-icon" />
    <ul class="agent-chat__features">
      <li><CommentOutlined /> 文档生成</li>
      <li><ThunderboltOutlined /> 多轮对话</li>
      <li><UnorderedListOutlined /> 持续优化</li>
    </ul>
    <p class="agent-chat__hint">
      平台不提供内置大模型。请点击右上角用户名 →「模型配置」添加 API 与密钥，再回到此处选择模型并生成用例。
    </p>
  </div>
</template>

<style scoped lang="scss">
.agent-chat__welcome {
  padding: 24px 16px;
  text-align: center;
  color: #8c8c8c;
}

.agent-chat__welcome-icon {
  font-size: 48px;
  color: #d9d9d9;
  margin-bottom: 12px;
}

.agent-chat__features {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  line-height: 2;
  text-align: left;
  max-width: 220px;
  margin-left: auto;
  margin-right: auto;
}

.agent-chat__hint {
  margin: 16px auto 0;
  max-width: 300px;
  font-size: 12px;
  line-height: 1.55;
  color: #bfbfbf;
}
</style>
