<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import type { AdminUserRow } from '@/api/adminUsers'
import {
  fetchAdminUserList,
  setAdminUserActive,
  deleteAdminUser,
} from '@/api/adminUsers'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.currentUser?.id ?? null)

const userList = ref<AdminUserRow[]>([])
const loading = ref(false)

const searchForm = reactive({
  username: '',
  status: undefined as undefined | 'active' | 'inactive',
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

// ant-design-vue 4 的 #bodyCell 以 column.dataIndex 区分列（与官网 Table 示例一致）
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 72 },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 130, ellipsis: true },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname', width: 130, ellipsis: true },
  { title: '用户类型', dataIndex: 'user_type', key: 'user_type', width: 110 },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 88 },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '最后登录', dataIndex: 'last_login_at', key: 'last_login_at', width: 170 },
  { title: '操作', dataIndex: 'action', key: 'action', width: 200, fixed: 'right' as const },
]

function formatTime(v: string | null) {
  if (!v) return '-'
  try {
    return new Date(v).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return v
  }
}

function isSelf(row: AdminUserRow) {
  return currentUserId.value !== null && row.id === currentUserId.value
}

const loadData = async () => {
  loading.value = true
  try {
    const isActive =
      searchForm.status === 'active' ? true : searchForm.status === 'inactive' ? false : undefined
    const res = await fetchAdminUserList({
      page: pagination.current,
      size: pagination.pageSize,
      username: searchForm.username.trim() || undefined,
      is_active: isActive,
    })
    if (res.code === 200 || res.code === 0) {
      const d = res.data!
      userList.value = d.items
      pagination.total = d.total
    }
  } catch {
    // 错误提示由 request 拦截器处理
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handlePaginationChange = (page: number, pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.current = page
  loadData()
}

const handleStatusChange = async (record: AdminUserRow, active: boolean) => {
  if (isSelf(record) && !active) {
    message.warning('不能禁用自己的账号')
    return
  }
  try {
    await setAdminUserActive(record.id, active)
    message.success(active ? '已启用' : '已禁用')
    await loadData()
  } catch {
    /* toast 由拦截器 */
  }
}

const handleDelete = (record: AdminUserRow) => {
  if (isSelf(record)) {
    message.warning('不能删除自己的账号')
    return
  }
  Modal.confirm({
    title: '确认删除该用户？',
    content: `将软删除用户「${record.username}」，删除后不可恢复登录。`,
    okText: '删除',
    okButtonProps: { type: 'primary', danger: true },
    cancelText: '取消',
    async onOk() {
      await deleteAdminUser(record.id)
      message.success('已删除')
      await loadData()
    },
  })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="users">
    <a-card class="main-card" :bordered="false">
      <div class="block search-row">
        <a-space wrap :size="12">
          <a-input
            v-model:value="searchForm.username"
            placeholder="用户名"
            allow-clear
            style="width: 220px"
            @pressEnter="handleSearch"
          />
          <a-select
            v-model:value="searchForm.status"
            placeholder="状态"
            allow-clear
            style="width: 120px"
          >
            <a-select-option value="active">启用</a-select-option>
            <a-select-option value="inactive">禁用</a-select-option>
          </a-select>
          <a-button type="primary" @click="handleSearch"><SearchOutlined />搜索</a-button>
        </a-space>
      </div>

      <div class="block table-block">
        <a-table
          :columns="columns"
          :data-source="userList"
          :loading="loading"
          :pagination="false"
          :scroll="{ x: 1000 }"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'user_type'">
              <a-tag :color="record.user_type === 'admin' ? 'red' : 'blue'">
                {{ record.user_type === 'admin' ? '管理员' : '普通用户' }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'orange'">
                {{ record.is_active ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'created_at'">
              {{ formatTime(record.created_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'last_login_at'">
              {{ formatTime(record.last_login_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-space :size="4" wrap>
                <a-button
                  v-if="!record.is_active"
                  type="link"
                  size="small"
                  :disabled="isSelf(record)"
                  @click="handleStatusChange(record, true)"
                >
                  启用
                </a-button>
                <a-button
                  v-if="record.is_active"
                  type="link"
                  size="small"
                  :disabled="isSelf(record)"
                  @click="handleStatusChange(record, false)"
                >
                  禁用
                </a-button>
                <a-button type="link" danger size="small" :disabled="isSelf(record)" @click="handleDelete(record)">
                  删除
                </a-button>
              </a-space>
            </template>
            <template v-else-if="column.dataIndex">
              {{
                (record as AdminUserRow)[column.dataIndex as keyof AdminUserRow] == null ||
                (record as AdminUserRow)[column.dataIndex as keyof AdminUserRow] === ''
                  ? '-'
                  : String((record as AdminUserRow)[column.dataIndex as keyof AdminUserRow])
              }}
            </template>
          </template>
        </a-table>
      </div>

      <div class="block pagination-row">
        <a-pagination
          :current="pagination.current"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(total: number) => `共 ${total} 条`"
          :page-size-options="['10', '20', '50']"
          @change="handlePaginationChange"
        />
      </div>
    </a-card>
  </div>
</template>

<style lang="scss" scoped>
.users {
  padding: 0;
}
.main-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.block + .block {
  margin-top: 16px;
}
.search-row {
  padding-bottom: 4px;
}
.pagination-row {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
