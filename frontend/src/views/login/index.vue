<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const rememberMe = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应在6-20个字符之间', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async (values: any) => {
  try {
    loading.value = true
    
    // 调用登录API
    await authStore.login({
      username: values.username,
      password: values.password
    })
    
    message.success('登录成功！')
    
    // 记住我功能
    if (rememberMe.value) {
      localStorage.setItem('remember_username', values.username)
    } else {
      localStorage.removeItem('remember_username')
    }
    
    // 跳转到管理后台
    router.push('/')
  } catch (error: any) {
    console.error('登录错误:', error)
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 处理表单提交失败
const handleLoginFailed = (errorInfo: any) => {
  console.log('表单验证失败:', errorInfo)
}

// 页面加载时初始化
onMounted(() => {
  // 恢复记住的用户名
  const rememberedUsername = localStorage.getItem('remember_username')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
  
  // 如果已经登录，直接跳转
  if (authStore.isAuthenticated) {
    router.push('/')
  }
})
</script>

<template>
  <div class="login-container">
    <a-card class="login-card" :bordered="false">
      <div class="login-title">密码登录</div>
      
      <a-form
        :model="loginForm"
        :rules="rules"
        @finish="handleLogin"
        @finishFailed="handleLoginFailed"
        layout="vertical"
        size="large"
        class="login-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="loginForm.username"
            placeholder="请输入用户名"
            size="large"
          />
        </a-form-item>
        
        <a-form-item name="password">
          <a-input-password
            v-model:value="loginForm.password"
            placeholder="请输入密码"
            size="large"
          />
        </a-form-item>
        
        <a-form-item>
          <a-row justify="space-between" align="middle">
            <a-col>
              <a-checkbox v-model:checked="rememberMe">
                记住我
              </a-checkbox>
            </a-col>
            <a-col>
              <a href="#" @click.prevent>忘记密码？</a>
            </a-col>
          </a-row>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
            size="large"
            class="login-button"
          >
            {{ loading ? '登录中...' : '确认' }}
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.login-title {
  font-size: 20px;
  font-weight: 600;
  color: #2C5AA0;
  margin-bottom: 32px;
  text-align: center;
}

.login-form {
  width: 100%;
}
</style>
