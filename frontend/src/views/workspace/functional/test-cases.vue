<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ModuleTree from '@/components/business/ModuleTree.vue'
import type { ProjectModuleNode } from '@/api/project-modules'

const route = useRoute()

const projectId = computed(() => {
  const raw = route.params.projectId
  const s = Array.isArray(raw) ? raw[0] : raw
  return s ? String(s) : ''
})

const projectIdNum = computed(() => {
  const id = projectId.value
  if (!id || !/^\d+$/.test(id)) return 0
  return Number(id)
})

const selectedModuleId = ref<number | null>(null)
const selectedModule = ref<ProjectModuleNode | null>(null)

function onModuleSelect(node: ProjectModuleNode) {
  selectedModule.value = node
}

watch(projectIdNum, () => {
  selectedModuleId.value = null
  selectedModule.value = null
})
</script>

<template>
  <div class="cases-shell">
    <div v-if="projectIdNum <= 0" class="cases-shell__card">
      <h2 class="cases-shell__title">测试用例</h2>
      <p class="cases-shell__desc">无效的项目 ID，请从「我的项目」重新进入。</p>
    </div>

    <div v-else class="cases-shell__layout">
      <aside class="cases-shell__aside" aria-label="模块目录">
        <ModuleTree
          :project-id="projectIdNum"
          v-model="selectedModuleId"
          title="模块目录"
          @select="onModuleSelect"
        />
      </aside>

      <section class="cases-shell__main">
        <div class="cases-shell__card cases-shell__card--main">
          <h2 class="cases-shell__title">测试用例</h2>
          <p v-if="!selectedModule" class="cases-shell__desc">
            请从左侧选择模块，右侧将展示该模块下的用例列表（待接入）。
          </p>
          <template v-else>
            <p class="cases-shell__meta">
              当前模块：
              <strong>{{ selectedModule.name }}</strong>
              <span class="cases-shell__id">#{{ selectedModule.id }}</span>
            </p>
            <p class="cases-shell__desc">用例列表、筛选与编辑将在此区域接入。</p>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.cases-shell {
  width: 100%;
  max-width: none;
  min-width: 0;
  box-sizing: border-box;
}

.cases-shell__layout {
  display: flex;
  align-items: stretch;
  gap: 16px;
  min-height: min(560px, calc(100vh - 140px));
}

.cases-shell__aside {
  flex: 0 0 288px;
  width: 288px;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.cases-shell__main {
  flex: 1;
  min-width: 0;
}

.cases-shell__card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.cases-shell__card--main {
  min-height: 100%;
  box-sizing: border-box;
}

.cases-shell__title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.cases-shell__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.55);
}

.cases-shell__meta {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.75);
}

.cases-shell__id {
  margin-left: 8px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
