<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'

// 系统配置表单
const configForm = reactive({
  siteName: 'NEXTest',
  siteDescription: 'Python毕业设计项目平台',
  siteLogo: '',
  siteKeywords: 'Python,毕业设计,项目,教程',
  adminEmail: 'admin@nextest.com',
  maxFileSize: 10,
  allowRegistration: true,
  emailVerification: true,
  maintenanceMode: false
})

// 保存配置
const handleSave = () => {
  message.success('配置保存成功')
}

// 重置配置
const handleReset = () => {
  message.info('配置已重置')
}

// 清除缓存
const handleClearCache = () => {
  message.success('缓存清除成功')
}
</script>

<template>
  <div class="system">

    <!-- 系统配置 -->
    <a-card class="config-card">
      <a-form
        :model="configForm"
        layout="vertical"
        @finish="handleSave"
      >
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="网站名称">
              <a-input v-model:value="configForm.siteName" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="管理员邮箱">
              <a-input v-model:value="configForm.adminEmail" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="网站描述">
          <a-textarea 
            v-model:value="configForm.siteDescription"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="网站关键词">
          <a-input v-model:value="configForm.siteKeywords" />
        </a-form-item>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="最大文件上传大小(MB)">
              <a-input-number 
                v-model:value="configForm.maxFileSize"
                :min="1"
                :max="100"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="网站状态">
              <a-switch 
                v-model:checked="configForm.maintenanceMode"
                checked-children="维护模式"
                un-checked-children="正常运行"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="允许用户注册">
              <a-switch v-model:checked="configForm.allowRegistration" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="邮箱验证">
              <a-switch v-model:checked="configForm.emailVerification" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit">
              <SaveOutlined />
              保存配置
            </a-button>
            <a-button @click="handleReset">
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 系统操作 -->
    <a-card class="operation-card">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-card size="small" class="operation-item">
            <div class="operation-content">
              <div class="operation-icon">
                <ReloadOutlined />
              </div>
              <div class="operation-info">
                <div class="operation-title">清除缓存</div>
                <div class="operation-desc">清除系统缓存，释放内存</div>
              </div>
              <a-button type="primary" @click="handleClearCache">
                执行
              </a-button>
            </div>
          </a-card>
        </a-col>
        
        <a-col :span="8">
          <a-card size="small" class="operation-item">
            <div class="operation-content">
              <div class="operation-icon">
                <SettingOutlined />
              </div>
              <div class="operation-info">
                <div class="operation-title">系统重启</div>
                <div class="operation-desc">重启系统服务</div>
              </div>
              <a-button danger>
                执行
              </a-button>
            </div>
          </a-card>
        </a-col>
        
        <a-col :span="8">
          <a-card size="small" class="operation-item">
            <div class="operation-content">
              <div class="operation-icon">
                <DatabaseOutlined />
              </div>
              <div class="operation-info">
                <div class="operation-title">数据库备份</div>
                <div class="operation-desc">备份数据库数据</div>
              </div>
              <a-button>
                执行
              </a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<style lang="scss" scoped>
.system {
  padding: 0;
}


.config-card,
.operation-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.operation-item {
  height: 120px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  :deep(.ant-card-body) {
    height: 100%;
    padding: 16px;
  }
}

.operation-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.operation-icon {
  font-size: 24px;
  color: #1890ff;
  text-align: center;
}

.operation-info {
  flex: 1;
  text-align: center;
}

.operation-title {
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.operation-desc {
  font-size: 12px;
  color: #8c8c8c;
}
</style>
