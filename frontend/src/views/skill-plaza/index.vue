<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { BarChartOutlined, MessageOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { listSkillPlaza } from '@/api/skillPlaza'
import type { SkillPlazaItem } from '@/schemas/skill'

const router = useRouter()

const loading = ref(false)
const items = ref<SkillPlazaItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const keyword = ref('')

async function load() {
  loading.value = true
  try {
    const res = await listSkillPlaza({
      page: page.value,
      size: pageSize.value,
      q: keyword.value.trim() || undefined
    })
    items.value = res.data?.items ?? []
    total.value = res.data?.total ?? 0
  } catch {
    message.error('加载技能列表失败')
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})

watch([page, pageSize], () => {
  void load()
})

let searchTimer: ReturnType<typeof setTimeout> | null = null
function onKeywordInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    void load()
  }, 360)
}

function goAgent(skillId: string) {
  router.push({ path: '/agent', query: { skill: skillId } })
}
</script>

<template>
  <div class="skill-plaza">
    <div class="skill-plaza__hero">
      <h1 class="skill-plaza__title">技能广场</h1>
      <p class="skill-plaza__sub">浏览已上架技能，在卡片中查看说明并前往测试智能体开始对话。</p>
      <a-input
        v-model:value="keyword"
        allow-clear
        size="large"
        placeholder="搜索技能名称、描述或 skill_id…"
        class="skill-plaza__search"
        @input="onKeywordInput"
      />
    </div>

    <a-spin :spinning="loading">
      <div v-if="!items.length && !loading" class="skill-plaza__empty">
        <a-empty description="暂无已上架技能" />
      </div>
      <a-row v-else :gutter="[16, 16]">
        <a-col v-for="row in items" :key="row.id" class="skill-plaza__col" :xs="24" :sm="12" :lg="8">
          <div class="skill-card">
            <div class="skill-card__head">
              <div class="skill-card__avatar" aria-hidden="true">
                <RobotOutlined />
              </div>
              <div class="skill-card__head-text">
                <span class="skill-card__title">{{ row.name }}</span>
              </div>
            </div>

            <p class="skill-card__desc">{{ row.description || '暂无描述' }}</p>

            <div class="skill-card__capabilities">
              <span class="skill-card__caps-label">核心能力：</span>
              <div class="skill-card__tags">
                <template v-if="row.capability_tags?.length">
                  <span v-for="tag in row.capability_tags" :key="tag" class="skill-card__pill">{{ tag }}</span>
                </template>
                <span v-else class="skill-card__pill skill-card__pill--muted">—</span>
              </div>
            </div>

            <div class="skill-card__stats">
              <span class="skill-card__stat-item">
                <BarChartOutlined class="skill-card__stat-icon" />
                {{ row.use_count }}
              </span>
            </div>

            <div class="skill-card__foot">
              <span
                class="skill-card__status"
                :class="{ 'skill-card__status--on': row.runtime_available }"
              >
                <span class="skill-card__status-dot" aria-hidden="true" />
                {{ row.runtime_available ? '可用' : '不可用' }}
              </span>
              <a-button
                type="primary"
                class="skill-card__cta"
                :disabled="!row.runtime_available"
                @click="goAgent(row.skill_id)"
              >
                <MessageOutlined />
                开始对话
              </a-button>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-spin>

    <div v-if="total > pageSize" class="skill-plaza__pager">
      <a-pagination
        v-model:current="page"
        v-model:page-size="pageSize"
        :total="total"
        :show-size-changer="true"
        :page-size-options="['12', '24', '48']"
        show-less-items
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.skill-plaza {
  width: 100%;
  box-sizing: border-box;
}

.skill-plaza__hero {
  margin-bottom: 20px;
}

.skill-plaza__title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 8px;
}

.skill-plaza__sub {
  color: #666;
  margin: 0 0 16px;
  font-size: 14px;
}

.skill-plaza__search {
  max-width: 520px;
}

.skill-plaza__empty {
  padding: 48px 0;
}

.skill-plaza__pager {
  margin-top: 24px;
  text-align: center;
}

.skill-plaza__col {
  display: flex;
}

.skill-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 18px 20px;
  background: #fff;
  border: 1px solid #91caff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(22, 119, 255, 0.06);
  min-height: 100%;
  box-sizing: border-box;
}

.skill-card__head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.skill-card__avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f0ebff 0%, #e6f4ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #1677ff;
}

.skill-card__head-text {
  min-width: 0;
  flex: 1;
}

.skill-card__title {
  font-weight: 600;
  font-size: 16px;
  color: #1f1f1f;
  line-height: 1.35;
}

.skill-card__desc {
  color: #8c8c8c;
  font-size: 13px;
  line-height: 1.55;
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-card__capabilities {
  margin-bottom: 12px;
}

.skill-card__caps-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #434343;
  margin-bottom: 8px;
}

.skill-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-card__pill {
  font-size: 12px;
  line-height: 1;
  padding: 5px 10px;
  border-radius: 999px;
  background: #f5f5f5;
  color: #595959;
}

.skill-card__pill--muted {
  color: #bfbfbf;
}

.skill-card__stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 16px;
}

.skill-card__stat-icon {
  margin-right: 4px;
  color: #8c8c8c;
}

.skill-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 4px;
}

.skill-card__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #8c8c8c;
}

.skill-card__status--on {
  color: #52c41a;
}

.skill-card__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
}

.skill-card__status--on .skill-card__status-dot {
  background: #52c41a;
}

.skill-card__cta {
  height: 40px;
  padding: 0 20px;
  border-radius: 8px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
