<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  UserOutlined,
  ShoppingOutlined,
  DollarOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'

// 统计数据
const stats = ref([
  {
    title: '总用户数',
    value: 1234,
    icon: UserOutlined,
    color: '#1890ff',
    change: '+12%'
  },
  {
    title: '商品总数',
    value: 567,
    icon: ShoppingOutlined,
    color: '#52c41a',
    change: '+8%'
  },
  {
    title: '总销售额',
    value: '¥89,123',
    icon: DollarOutlined,
    color: '#faad14',
    change: '+15%'
  },
  {
    title: '今日访问',
    value: 2341,
    icon: EyeOutlined,
    color: '#f5222d',
    change: '+5%'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    type: 'user',
    title: '新用户注册',
    description: '用户 "张三" 刚刚注册了账号',
    time: '2分钟前'
  },
  {
    id: 2,
    type: 'order',
    title: '新订单',
    description: '用户 "李四" 下单购买了 "Python教程"',
    time: '5分钟前'
  },
  {
    id: 3,
    type: 'goods',
    title: '商品更新',
    description: '商品 "Vue3实战" 价格已更新',
    time: '10分钟前'
  }
])

onMounted(() => {
  // 这里可以加载真实数据
})
</script>

<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <a-row :gutter="[16, 16]" class="stats-row">
      <a-col 
        v-for="stat in stats" 
        :key="stat.title"
        :xs="24" 
        :sm="12" 
        :lg="6"
      >
        <a-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ color: stat.color }">
              <component :is="stat.icon" />
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
              <div class="stat-change" :class="{ positive: stat.change.startsWith('+') }">
                {{ stat.change }}
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 内容区域 -->
    <a-row :gutter="[16, 16]" class="content-row">
      <!-- 最近活动 -->
      <a-col :xs="24" :lg="12">
        <a-card title="最近活动" class="activity-card">
          <a-list
            :dataSource="recentActivities"
            :loading="false"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span class="activity-title">{{ item.title }}</span>
                  </template>
                  <template #description>
                    <span class="activity-description">{{ item.description }}</span>
                    <div class="activity-time">{{ item.time }}</div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>

      <!-- 快捷操作 -->
      <a-col :xs="24" :lg="12">
        <a-card title="快捷操作" class="quick-actions-card">
          <a-row :gutter="[8, 8]">
            <a-col :span="12">
              <a-button type="primary" block size="large">
                添加商品
              </a-button>
            </a-col>
            <a-col :span="12">
              <a-button block size="large">
                用户管理
              </a-button>
            </a-col>
            <a-col :span="12">
              <a-button block size="large">
                订单管理
              </a-button>
            </a-col>
            <a-col :span="12">
              <a-button block size="large">
                系统设置
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<style lang="scss" scoped>
.dashboard {
  padding: 0;
}


.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  :deep(.ant-card-body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background: rgba(24, 144, 255, 0.1);
  border-radius: 12px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-title {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-change {
  font-size: 12px;
  font-weight: 500;
  
  &.positive {
    color: #52c41a;
  }
  
  &:not(.positive) {
    color: #f5222d;
  }
}

.content-row {
  margin-bottom: 24px;
}

.activity-card,
.quick-actions-card {
  height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  :deep(.ant-card-head) {
    border-bottom: 1px solid #f0f0f0;
  }
  
  :deep(.ant-card-body) {
    height: calc(100% - 57px);
    overflow-y: auto;
  }
}

.activity-title {
  font-weight: 500;
  color: #262626;
}

.activity-description {
  color: #8c8c8c;
  font-size: 14px;
}

.activity-time {
  color: #bfbfbf;
  font-size: 12px;
  margin-top: 4px;
}

.quick-actions-card {
  :deep(.ant-card-body) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
