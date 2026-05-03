<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import AuthBrandingAside from '@/components/auth/AuthBrandingAside.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit() {
  try {
    loading.value = true
    await authStore.login({
      username: form.username.trim(),
      password: form.password,
    })
    message.success('登录成功')
    router.push('/agent')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goRegister() {
  router.push('/register')
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/agent')
  }
})
</script>

<template>
  <div class="auth-page">
    <AuthBrandingAside />
    <div class="auth-main">
      <div class="auth-panel">
        <h2 class="auth-heading">欢迎回来</h2>
        <p class="auth-sub">登录您的账户，开启智能体协作之旅</p>

        <a-form
          :model="form"
          :rules="rules"
          layout="vertical"
          class="auth-form"
          @finish="handleSubmit"
        >
          <a-form-item name="username">
            <a-input
              v-model:value="form.username"
              size="large"
              placeholder="请输入用户名"
              class="auth-input"
              @pressEnter="handleSubmit"
            >
              <template #prefix>
                <UserOutlined class="input-icon" />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item name="password">
            <a-input-password
              v-model:value="form.password"
              size="large"
              placeholder="请输入密码"
              class="auth-input"
              @pressEnter="handleSubmit"
            >
              <template #prefix>
                <LockOutlined class="input-icon" />
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              block
              size="large"
              class="btn-primary"
              :loading="loading"
            >
              <LoginOutlined />
              登录
            </a-button>
          </a-form-item>
        </a-form>

        <p class="auth-footer-link">
          还没有账户？
          <a type="link" class="link" @click="goRegister">立即注册</a>
        </p>

        <p class="copyright">© 2026 NexTest. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.auth-page {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: #fff;
}

.auth-main {
  flex: 0 0 50%;
  width: 50%;
  min-width: 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: #fafafa;
}

@media (max-width: 900px) {
  .auth-main {
    flex: 1 1 100%;
    width: 100%;
  }
}

.auth-panel {
  width: 100%;
  max-width: 400px;
}

.auth-heading {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.auth-sub {
  margin: 0 0 32px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.auth-form {
  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }
}

.auth-input {
  border-radius: 10px;
  :deep(.ant-input),
  :deep(.ant-input-password) {
    border-radius: 10px;
  }
}

.input-icon {
  color: #9ca3af;
}

.btn-primary {
  border-radius: 10px;
  height: 44px;
  font-weight: 500;
  background: #2563eb;
  border-color: #2563eb;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  &:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
  }
}

.auth-footer-link {
  margin: 24px 0 0;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.link {
  color: #2563eb;
  cursor: pointer;
  margin-left: 4px;
  &:hover {
    color: #1d4ed8;
  }
}

.copyright {
  margin: 32px 0 0;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>
