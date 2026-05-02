<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/sidebar/index.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const collapsed = ref(false)
const currentUser = computed(() => authStore.currentUser)

function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

function handleResize() {
  if (window.innerWidth < 768) {
    collapsed.value = true
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <a-layout style="min-height: 100vh">
    <Sidebar
      :collapsed="collapsed"
      :current-user="currentUser"
      @toggle-collapsed="toggleCollapsed"
    />

    <a-layout-content
      :style="{
        marginLeft: collapsed ? '80px' : '260px',
        transition: 'margin-left 0.2s',
        padding: 0,
        minHeight: '100vh',
        background: '#f7fafc',
      }"
    >
      <router-view />
    </a-layout-content>
  </a-layout>
</template>

<style lang="scss" scoped>
// 布局样式
</style>
