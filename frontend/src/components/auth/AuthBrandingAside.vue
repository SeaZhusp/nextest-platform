<script setup lang="ts">
import { TeamOutlined, AppstoreOutlined, DatabaseOutlined } from '@ant-design/icons-vue'

const features = [
  { icon: AppstoreOutlined, text: '智能体编排' },
  { icon: TeamOutlined, text: '多智能体协作' },
  { icon: DatabaseOutlined, text: '工作流可视化' },
]
</script>

<template>
  <aside class="brand-aside">
    <div class="brand-bg" aria-hidden="true">
      <div class="shape shape-1" />
      <div class="shape shape-2" />
    </div>
    <div class="brand-inner">
      <div class="logo-wrap">
        <div class="logo-icon">
          <TeamOutlined />
        </div>
      </div>
      <h1 class="brand-title">NexTest</h1>
      <p class="brand-sub">多智能体协作平台</p>
      <p class="brand-desc">
        专业的 AI 智能体与协作工具，让多个智能体协同工作，提升任务执行效率。
      </p>
      <div class="feature-tags">
        <div v-for="(f, i) in features" :key="i" class="feature-tag">
          <component :is="f.icon" class="feature-icon" />
          <span>{{ f.text }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.brand-aside {
  position: relative;
  flex: 0 0 50%;
  width: 50%;
  min-width: 0;
  box-sizing: border-box;
  background: linear-gradient(160deg, #1d4ed8 0%, #2563eb 45%, #3b82f6 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  overflow: hidden;
}

.brand-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 32px;
  opacity: 0.12;
  background: #fff;
}

.shape-1 {
  width: 280px;
  height: 280px;
  top: -80px;
  right: -60px;
  transform: rotate(12deg);
}

.shape-2 {
  width: 420px;
  height: 420px;
  bottom: -120px;
  left: -100px;
  transform: rotate(-8deg);
}

.brand-inner {
  position: relative;
  z-index: 1;
  max-width: 400px;
}

.logo-wrap {
  margin-bottom: 20px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  backdrop-filter: blur(8px);
}

.brand-title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.brand-sub {
  margin: 0 0 16px;
  font-size: 16px;
  opacity: 0.95;
  font-weight: 500;
}

.brand-desc {
  margin: 0 0 28px;
  font-size: 14px;
  line-height: 1.7;
  opacity: 0.88;
}

.feature-tags {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 14px;
  width: fit-content;
  max-width: 100%;
}

.feature-icon {
  font-size: 16px;
  opacity: 0.95;
}

@media (max-width: 900px) {
  .brand-aside {
    display: none;
  }
}
</style>
