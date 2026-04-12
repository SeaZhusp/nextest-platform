<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  StopOutlined
} from '@ant-design/icons-vue'
import LlmProviderIcon from '@/components/LlmProviderIcon.vue'
import { DEFAULT_BASE, PROVIDERS, providerLabel, providerMeta } from '@/config/llmProviders'
import {
  createUserLlmProfile,
  deleteUserLlmProfile,
  getUserLlmProfile,
  listUserLlmProfiles,
  setUserLlmProfileActive,
  testLlmConnection,
  testLlmConnectionById,
  updateUserLlmProfile
} from '@/api/userLlmProfiles'
import type { UserLlmProfileOut } from '@/schemas/userLlmProfile'

const loading = ref(false)
const items = ref<UserLlmProfileOut[]>([])

const modalOpen = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const testing = ref(false)
const form = ref({
  provider: 'deepseek' as string,
  api_key: '',
  api_base: DEFAULT_BASE.deepseek,
  model_name: 'deepseek-chat',
  display_name: '',
  is_active: true
})

const revealKey = ref<Record<number, string | undefined>>({})
const showPlain = ref<Record<number, boolean>>({})

const modalTitle = computed(() =>
  editingId.value != null ? '编辑 API Key 配置' : '添加 API Key 配置'
)

async function load() {
  loading.value = true
  try {
    const res = await listUserLlmProfiles()
    items.value = res.data?.items ?? []
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})

function resetForm() {
  form.value = {
    provider: 'deepseek',
    api_key: '',
    api_base: DEFAULT_BASE.deepseek,
    model_name: 'deepseek-chat',
    display_name: '',
    is_active: true
  }
}

function onProviderChange() {
  const p = form.value.provider
  form.value.api_base = DEFAULT_BASE[p] ?? ''
}

function openAdd() {
  editingId.value = null
  resetForm()
  modalOpen.value = true
}

async function openEdit(row: UserLlmProfileOut) {
  editingId.value = row.id
  try {
    const res = await getUserLlmProfile(row.id)
    const d = res.data
    if (!d) return
    form.value = {
      provider: d.provider || 'other',
      api_key: d.api_key,
      api_base: d.api_base,
      model_name: d.model_name,
      display_name: d.display_name,
      is_active: d.is_active
    }
    modalOpen.value = true
  } catch {
    /* 拦截器 */
  }
}

async function toggleReveal(row: UserLlmProfileOut) {
  const id = row.id
  if (showPlain.value[id]) {
    showPlain.value[id] = false
    return
  }
  if (revealKey.value[id] == null) {
    try {
      const res = await getUserLlmProfile(id)
      if (res.data?.api_key) revealKey.value[id] = res.data.api_key
    } catch {
      return
    }
  }
  showPlain.value[id] = true
}

function displayKey(row: UserLlmProfileOut) {
  if (showPlain.value[row.id] && revealKey.value[row.id]) {
    return revealKey.value[row.id]
  }
  return row.api_key_masked
}

async function handleTestForm() {
  const { api_base, model_name, api_key } = form.value
  if (!api_base.trim() || !model_name.trim() || !api_key.trim()) {
    message.warning('请填写 API 地址、模型名与 API Key 后再测试')
    return
  }
  testing.value = true
  try {
    const res = await testLlmConnection({
      api_base: api_base.trim(),
      model_name: model_name.trim(),
      api_key: api_key.trim()
    })
    if (res.data?.ok) message.success(res.data.message || '连接成功')
  } catch {
    /* 业务错误已提示 */
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  const { provider, api_key, api_base, model_name, display_name, is_active } = form.value
  if (!provider || !api_key.trim() || !api_base.trim() || !model_name.trim()) {
    message.warning('请填写模型提供商、API Key、API 地址与模型名称')
    return
  }
  submitting.value = true
  try {
    if (editingId.value != null) {
      await updateUserLlmProfile(editingId.value, {
        provider,
        api_key: api_key.trim(),
        api_base: api_base.trim(),
        model_name: model_name.trim(),
        display_name: display_name.trim() || undefined,
        is_active
      })
      message.success('已保存')
    } else {
      await createUserLlmProfile({
        provider,
        api_key: api_key.trim(),
        api_base: api_base.trim(),
        model_name: model_name.trim(),
        display_name: display_name.trim() || undefined,
        is_active
      })
      message.success('已添加')
    }
    modalOpen.value = false
    revealKey.value = {}
    showPlain.value = {}
    await load()
  } catch {
    /* */
  } finally {
    submitting.value = false
  }
}

async function handleTestCard(row: UserLlmProfileOut) {
  const hide = message.loading('正在测试连接…', 0)
  try {
    const res = await testLlmConnectionById(row.id)
    hide()
    if (res.data?.ok) message.success(res.data.message || '连接成功')
  } catch {
    hide()
  }
}

async function toggleActive(row: UserLlmProfileOut) {
  try {
    await setUserLlmProfileActive(row.id, !row.is_active)
    message.success(row.is_active ? '已禁用' : '已启用')
    await load()
  } catch {
    /* */
  }
}

function confirmDelete(row: UserLlmProfileOut) {
  Modal.confirm({
    title: '删除该配置？',
    content: `确定删除「${row.display_name}」吗？此操作不可恢复。`,
    okText: '删除',
    okType: 'danger',
    onOk: () =>
      deleteUserLlmProfile(row.id).then(async () => {
        message.success('已删除')
        await load()
      })
  })
}
</script>

<template>
  <div class="llm-page">
    <div class="llm-page__head">
      <div>
        <h1 class="llm-page__title">模型配置</h1>
        <p class="llm-page__desc">
          管理自备大模型（OpenAI 兼容接口）。平台不提供内置模型；卡片中可测试连接、编辑、启用/禁用或删除。
        </p>
      </div>
      <a-button type="primary" @click="openAdd">
        <template #icon>
          <PlusOutlined />
        </template>
        添加配置
      </a-button>
    </div>

    <a-spin :spinning="loading">
      <div v-if="!items.length && !loading" class="llm-page__empty">
        <ApiOutlined class="llm-page__empty-icon" />
        <p>暂无配置，请点击「添加配置」</p>
      </div>

      <a-row v-else :gutter="[16, 16]">
        <a-col
          v-for="row in items"
          :key="row.id"
          :xs="24"
          :sm="24"
          :md="12"
          :lg="8"
          :xl="6"
          :xxl="6"
        >
          <div class="llm-card" :class="{ 'llm-card--inactive': !row.is_active }">
            <div class="llm-card__head">
              <div class="llm-card__brand">
                <div class="llm-card__logo-wrap">
                  <LlmProviderIcon :meta="providerMeta(row.provider)" :size="22" />
                </div>
                <div class="llm-card__titles">
                  <div class="llm-card__provider">{{ providerLabel(row.provider) }}</div>
                  <div class="llm-card__name" :title="row.display_name">{{ row.display_name }}</div>
                </div>
              </div>
              <a-tag :color="row.is_active ? 'success' : 'default'">
                {{ row.is_active ? '已启用' : '已禁用' }}
              </a-tag>
            </div>

            <div class="llm-card__body">
              <div class="llm-card__row">
                <span class="llm-card__k">API Key</span>
                <span class="llm-card__v llm-card__v--mono">
                  {{ displayKey(row) }}
                </span>
                <a-button type="text" size="small" class="llm-card__eye" @click="toggleReveal(row)">
                  <EyeOutlined v-if="!showPlain[row.id]" />
                  <EyeInvisibleOutlined v-else />
                </a-button>
              </div>
              <div class="llm-card__row">
                <span class="llm-card__k">模型</span>
                <span class="llm-card__v" :title="row.model_name">{{ row.model_name }}</span>
              </div>
              <div class="llm-card__row llm-card__row--addr">
                <span class="llm-card__k">地址</span>
                <span class="llm-card__v" :title="row.api_base">{{ row.api_base }}</span>
              </div>
            </div>

            <div class="llm-card__foot">
              <a-button type="link" size="small" @click="handleTestCard(row)">
                <ApiOutlined /> 测试
              </a-button>
              <a-button type="link" size="small" @click="openEdit(row)">
                <EditOutlined /> 编辑
              </a-button>
              <a-button type="link" size="small" @click="toggleActive(row)">
                <CheckCircleOutlined v-if="!row.is_active" />
                <StopOutlined v-else />
                {{ row.is_active ? '禁用' : '启用' }}
              </a-button>
              <a-button type="link" size="small" danger @click="confirmDelete(row)">
                <DeleteOutlined /> 删除
              </a-button>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-spin>

    <a-modal
      v-model:open="modalOpen"
      :title="modalTitle"
      width="560px"
      :confirm-loading="submitting"
      :mask-closable="false"
      destroy-on-close
      :footer="null"
      @cancel="modalOpen = false"
    >
      <a-form layout="vertical" class="llm-modal-form">
        <a-form-item label="模型提供商" required>
          <a-select
            v-model:value="form.provider"
            placeholder="请选择"
            size="large"
            @change="onProviderChange"
          >
            <a-select-option v-for="p in PROVIDERS" :key="p.id" :value="p.id">
              <span class="llm-opt">
                <LlmProviderIcon :meta="p" :size="18" />
                {{ p.label }}
              </span>
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="API Key" required>
          <a-input-password v-model:value="form.api_key" placeholder="请输入 API Key" size="large" />
        </a-form-item>

        <a-form-item label="API 地址" required>
          <a-input v-model:value="form.api_base" placeholder="OpenAI 兼容 Base URL" size="large" />
        </a-form-item>

        <a-form-item label="模型名称" required>
          <a-input v-model:value="form.model_name" placeholder="如 deepseek-chat、qwen-max 等" size="large" />
        </a-form-item>

        <a-form-item label="显示名称">
          <a-input
            v-model:value="form.display_name"
            placeholder="可选，用于对话区下拉展示"
            size="large"
          />
        </a-form-item>

        <a-form-item label="启用状态">
          <a-switch v-model:checked="form.is_active" checked-children="开" un-checked-children="关" />
        </a-form-item>
      </a-form>

      <div class="llm-modal__footer">
        <a-button @click="modalOpen = false">取消</a-button>
        <a-button :loading="testing" @click="handleTestForm">测试连接</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSave">保存</a-button>
      </div>
    </a-modal>
  </div>
</template>

<style lang="scss" scoped>
.llm-page {
  width: 100%;
  max-width: none;
  box-sizing: border-box;
  padding: 0 0 32px;
}

.llm-page__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.llm-page__title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.llm-page__desc {
  margin: 0;
  max-width: none;
  font-size: 13px;
  line-height: 1.6;
  color: #8c8c8c;
}

.llm-page__empty {
  text-align: center;
  padding: 48px 16px;
  color: #bfbfbf;
  background: #fafafa;
  border-radius: 12px;
  border: 1px dashed #e8e8e8;
}

.llm-page__empty-icon {
  font-size: 40px;
  margin-bottom: 8px;
  display: block;
}

.llm-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  }

  &--inactive {
    opacity: 0.85;
    background: #fafafa;
  }
}

.llm-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 14px;
}

.llm-card__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.llm-card__logo-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #f5f5f5;
  overflow: hidden;
}

.llm-card__titles {
  min-width: 0;
}

.llm-card__provider {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
  line-height: 1.3;
}

.llm-card__name {
  font-size: 12px;
  color: #8c8c8c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.llm-card__body {
  flex: 1;
  font-size: 12px;
  color: #595959;
}

.llm-card__row {
  display: grid;
  grid-template-columns: 56px 1fr 32px;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;

  &--addr {
    grid-template-columns: 56px 1fr;
    align-items: start;

    .llm-card__v {
      word-break: break-all;
      line-height: 1.45;
    }
  }
}

.llm-card__k {
  color: #8c8c8c;
}

.llm-card__v {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &--mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 11px;
  }
}

.llm-card__eye {
  padding: 0 !important;
  height: 28px;
  width: 28px;
}

.llm-card__foot {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 2px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f5f5f5;

  :deep(.ant-btn) {
    padding: 0 6px;
  }
}

.llm-opt {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.llm-modal-form {
  margin-bottom: 8px;
}

.llm-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  margin-top: 8px;
}
</style>
