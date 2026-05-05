<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LeftOutlined, DownOutlined } from '@ant-design/icons-vue'
import { fetchProject } from '@/api/projects'
import type { ProjectRow } from '@/api/projects'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => {
  const raw = route.params.projectId
  const s = Array.isArray(raw) ? raw[0] : raw
  return s ? String(s) : ''
})

const project = ref<ProjectRow | null>(null)
const projectLoading = ref(false)

async function loadProject() {
  const id = projectId.value
  if (!id || !/^\d+$/.test(id)) {
    project.value = null
    return
  }
  projectLoading.value = true
  try {
    const res = await fetchProject(Number(id))
    if (res.code === 200 || res.code === 0) {
      project.value = res.data ?? null
    } else {
      project.value = null
    }
  } catch {
    project.value = null
  } finally {
    projectLoading.value = false
  }
}

watch(
  projectId,
  () => {
    void loadProject()
  },
  { immediate: true },
)

const projectTitle = computed(() => project.value?.name || `项目 #${projectId.value || '…'}`)

type NavChild = { key: string; label: string; name: string }
type NavItem = { key: string; label: string; children: NavChild[] }

const navItems = computed<NavItem[]>(() => {
  const pid = projectId.value
  if (!pid) return []
  return [
    {
      key: 'functional-test',
      label: '功能测试',
      children: [{ key: 'functional-test-cases', label: '测试用例', name: 'functional-test-cases' }],
    },
    {
      key: 'api-test',
      label: '接口测试',
      children: [
        { key: 'api-list', label: '接口列表', name: 'project-api-test-list' },
        { key: 'api-mock', label: 'Mock 服务', name: 'project-api-mock' },
      ],
    },
    {
      key: 'ui-test',
      label: 'UI 测试',
      children: [
        { key: 'ui-cases', label: '用例管理', name: 'project-ui-test-cases' },
        { key: 'ui-rec', label: '录制回放', name: 'project-ui-recording' },
      ],
    },
    {
      key: 'perf-test',
      label: '性能测试',
      children: [
        { key: 'perf-scn', label: '压测场景', name: 'project-perf-scenarios' },
        { key: 'perf-rep', label: '测试报告', name: 'project-perf-reports' },
      ],
    },
  ]
})

function isChildActive(item: NavItem): boolean {
  return item.children.some((c) => route.name === c.name)
}

function goChild(name: string) {
  const pid = projectId.value
  if (!pid) return
  void router.push({ name, params: { projectId: pid } })
}

function backToProjects() {
  void router.push({ name: 'projects' })
}
</script>

<template>
  <div class="pw">
    <header class="pw-header">
      <div class="pw-header__bar">
        <div class="pw-header__left">
          <a-button type="text" class="pw-back" @click="backToProjects">
            <LeftOutlined />
            我的项目
          </a-button>
          <span class="pw-header__sep" aria-hidden="true" />
          <a-spin v-if="projectLoading" size="small" />
          <span v-else class="pw-header__title" :title="projectTitle">{{ projectTitle }}</span>
        </div>

        <nav class="pw-nav" aria-label="项目内导航">
          <a-dropdown
            v-for="item in navItems"
            :key="item.key"
            :trigger="['click']"
            placement="bottomLeft"
          >
            <button
              type="button"
              class="pw-nav__trigger"
              :class="{ 'pw-nav__trigger--active': isChildActive(item) }"
            >
              {{ item.label }}
              <DownOutlined class="pw-nav__caret" />
            </button>
            <template #overlay>
              <a-menu @click="(e: { key: string | number }) => goChild(String(e.key))">
                <a-menu-item v-for="c in item.children" :key="c.name">
                  {{ c.label }}
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </nav>
      </div>
    </header>

    <main class="pw-main">
      <a-alert
        v-if="!projectLoading && projectId && /^\d+$/.test(projectId) && !project"
        type="warning"
        show-icon
        message="无法加载该项目"
        description="可能没有权限或项目不存在，请返回我的项目重试。"
        class="pw-alert"
      />
      <router-view />
    </main>
  </div>
</template>

<style lang="scss" scoped>
.pw {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  background: #f7fafc;
}

/* 低于 Modal 默认 z-index(1000) */
.pw-header {
  position: sticky;
  top: 0;
  z-index: 99;
  flex-shrink: 0;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.pw-header__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0 16px;
  min-height: 48px;
}

.pw-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.pw-back {
  flex-shrink: 0;
  padding: 4px 8px !important;
  color: rgba(0, 0, 0, 0.65) !important;

  &:hover {
    color: #1890ff !important;
  }
}

.pw-header__sep {
  width: 1px;
  height: 16px;
  background: #f0f0f0;
  flex-shrink: 0;
}

.pw-header__title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  max-width: min(360px, 40vw);
}

.pw-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.pw-nav__trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  margin: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.75);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;

  &:hover {
    background: #f5f5f5;
    color: #1890ff;
  }

  &--active {
    color: #1890ff;
    background: #e6f7ff;
    font-weight: 500;
  }
}

.pw-nav__caret {
  font-size: 10px;
  opacity: 0.55;
}

.pw-main {
  flex: 1;
  min-height: 0;
  min-width: 0;
  padding: 16px;
  box-sizing: border-box;
}

.pw-alert {
  margin-bottom: 16px;
  max-width: 720px;
}
</style>
