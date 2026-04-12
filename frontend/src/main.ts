import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './stores/auth'
import './style.css'
import 'ant-design-vue/dist/reset.css'
import '@/utils/patchAntdModal'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)

  const authStore = useAuthStore()
  await authStore.syncUserFromServerIfLoggedIn()

  app.use(router)
  app.use(Antd)
  app.mount('#app')
}

void bootstrap()
