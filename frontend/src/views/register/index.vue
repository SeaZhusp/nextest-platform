<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, UserAddOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import AuthBrandingAside from '@/components/auth/AuthBrandingAside.vue'
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  password_confirm: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 位', trigger: 'blur' },
  ],
  password_confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 位', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  if (form.password !== form.password_confirm) {
    message.error('两次输入的密码不一致')
    return
  }
  try {
    loading.value = true
    await authStore.register({
      username: form.username.trim(),
      password: form.password,
      password_confirm: form.password_confirm,
    })
    message.success('注册成功')
    router.push('/')
  } catch (e) {
    // 失败提示由 @/utils/request 拦截器统一处理，避免与页面内二次 toast 重复
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goLogin() {
  router.push('/login')
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/')
  }
})
</script>

<template>
  <div class="auth-page">
    <AuthBrandingAside />
    <div class="auth-main">
      <div class="auth-panel">
        <h2 class="auth-heading">创建账户</h2>
        <p class="auth-sub">填写信息，开启智能体协作之旅</p>

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
              placeholder="请输入用户名（3-50 个字符）"
              class="auth-input"
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
              placeholder="请设置密码（6-100 位）"
              class="auth-input"
            >
              <template #prefix>
                <LockOutlined class="input-icon" />
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item name="password_confirm">
            <a-input-password
              v-model:value="form.password_confirm"
              size="large"
              placeholder="请确认密码"
              class="auth-input"
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
              <UserAddOutlined />
              完成注册
            </a-button>
          </a-form-item>
        </a-form>

        <p class="auth-footer-link">
          已有账户？
          <a type="link" class="link" @click="goLogin">立即登录</a>
        </p>

        <p class="copyright">© 2026 NEXTest. 保留所有权利。</p>
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
  margin: 0 0 28px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.auth-form {
  :deep(.ant-form-item) {
    margin-bottom: 18px;
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
  margin: 8px 0 0;
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
  margin: 28px 0 0;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}
</style>
