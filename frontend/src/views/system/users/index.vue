<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  SearchOutlined,
  ReloadOutlined,
  SettingOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

interface UserItem {
  id: number
  username: string
  email: string
  avatar: string
  role: 'admin' | 'user'
  status: 'active' | 'inactive' | 'banned'
  createdAt: string
  lastLoginAt: string
  loginCount: number
}

const userList = ref<UserItem[]>([])
const loading = ref(false)
const selectedRowKeys = ref<number[]>([])

const searchForm = reactive({
  username: '',
  email: '',
  nickname: '',
  phone: '',
  gender: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

const columns = [
  { title: '用户信息', dataIndex: 'username', key: 'username', width: 200, slots: { customRender: 'userInfo' } },
  { title: '邮箱', dataIndex: 'email', key: 'email', width: 200 },
  { title: '角色', dataIndex: 'role', key: 'role', width: 100, slots: { customRender: 'role' } },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100, slots: { customRender: 'status' } },
  { title: '登录次数', dataIndex: 'loginCount', key: 'loginCount', width: 100 },
  { title: '最后登录', dataIndex: 'lastLoginAt', key: 'lastLoginAt', width: 150 },
  { title: '操作', key: 'action', width: 150, slots: { customRender: 'action' } }
]

const genderOptions = [
  { label: '全部', value: '' },
  { label: '男', value: 'male' },
  { label: '女', value: 'female' }
]

const statusOptions = [
  { label: '全部', value: '' },
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'inactive' }
]

const mockData: UserItem[] = [
  { id: 1, username: 'admin', email: 'admin@example.com', avatar: 'https://via.placeholder.com/40x40', role: 'admin', status: 'active', createdAt: '2024-01-01 00:00:00', lastLoginAt: '2024-01-20 10:30:00', loginCount: 156 },
  { id: 2, username: 'Myv666e3M', email: 'margaret.young@example.com', avatar: 'https://via.placeholder.com/40x40', role: 'user', status: 'active', createdAt: '2024-01-05 14:20:00', lastLoginAt: '2024-01-19 16:45:00', loginCount: 23 },
  { id: 3, username: 'jtCs', email: 'kenneth.perez@example.com', avatar: 'https://via.placeholder.com/40x40', role: 'user', status: 'inactive', createdAt: '2024-01-10 09:15:00', lastLoginAt: '2024-01-18 20:30:00', loginCount: 89 },
  { id: 4, username: 'kOKodgyNm1x7xJ', email: 'michael.wilson@example.com', avatar: 'https://via.placeholder.com/40x40', role: 'user', status: 'active', createdAt: '2024-01-12 11:20:00', lastLoginAt: '2024-01-19 13:30:00', loginCount: 45 }
]

const loadData = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    let filteredData = [...mockData]
    if (searchForm.username) filteredData = filteredData.filter(item => item.username.includes(searchForm.username))
    if (searchForm.email) filteredData = filteredData.filter(item => item.email.includes(searchForm.email))
    if (searchForm.status) filteredData = filteredData.filter(item => item.status === searchForm.status)
    const start = (pagination.current - 1) * pagination.pageSize
    const end = start + pagination.pageSize
    userList.value = filteredData.slice(start, end)
    pagination.total = filteredData.length
  } catch {
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, { username: '', email: '', nickname: '', phone: '', gender: '', status: '' })
  pagination.current = 1
  loadData()
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadData()
}

const handleSelectionChange = (keys: number[]) => {
  selectedRowKeys.value = keys
}

const handleAdd = () => message.info('添加用户')
const handleBatchDelete = () => {
  if (selectedRowKeys.value.length === 0) return message.warning('请选择要删除的用户')
  message.info(`批量删除 ${selectedRowKeys.value.length} 个用户`)
}
const handleEdit = (record: UserItem) => message.info(`编辑用户: ${record.username}`)
const handleDelete = (record: UserItem) => message.info(`删除用户: ${record.username}`)
const handleStatusChange = (record: UserItem, status: string) => {
  record.status = status as any
  message.success('状态更新成功')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="users">
    <a-card class="search-card" :bordered="false">
      <a-form :model="searchForm" class="search-form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-row :gutter="[16, 16]">
          <a-col :span="6"><a-form-item label="用户名" labelAlign="right"><a-input v-model:value="searchForm.username" placeholder="请输入用户名" @pressEnter="handleSearch" /></a-form-item></a-col>
          <a-col :span="6"><a-form-item label="邮箱" labelAlign="right"><a-input v-model:value="searchForm.email" placeholder="请输入邮箱" @pressEnter="handleSearch" /></a-form-item></a-col>
          <a-col :span="6"><a-form-item label="昵称" labelAlign="right"><a-input v-model:value="searchForm.nickname" placeholder="请输入昵称" @pressEnter="handleSearch" /></a-form-item></a-col>
          <a-col :span="6"><a-form-item label="手机号" labelAlign="right"><a-input v-model:value="searchForm.phone" placeholder="请输入手机号" @pressEnter="handleSearch" /></a-form-item></a-col>
          <a-col :span="6"><a-form-item label="性别" labelAlign="right"><a-select v-model:value="searchForm.gender" placeholder="请选择性别"><a-select-option v-for="option in genderOptions" :key="option.value" :value="option.value">{{ option.label }}</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="6"><a-form-item label="用户状态" labelAlign="right"><a-select v-model:value="searchForm.status" placeholder="请选择用户状态"><a-select-option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="12" class="search-actions"><a-space><a-button @click="handleReset">重置</a-button><a-button type="primary" @click="handleSearch"><SearchOutlined />搜索</a-button></a-space></a-col>
        </a-row>
      </a-form>
    </a-card>

    <a-card class="table-card" :bordered="false">
      <div class="action-bar">
        <a-space>
          <a-button type="primary" @click="handleAdd"><PlusOutlined />新增</a-button>
          <a-button danger :disabled="selectedRowKeys.length === 0" @click="handleBatchDelete"><DeleteOutlined />批量删除</a-button>
          <a-button @click="loadData"><ReloadOutlined />刷新</a-button>
          <a-button><SettingOutlined />列设</a-button>
        </a-space>
      </div>

      <a-table
        :columns="columns"
        :dataSource="userList"
        :loading="loading"
        :pagination="pagination"
        :rowSelection="{ selectedRowKeys: selectedRowKeys, onChange: handleSelectionChange }"
        @change="handleTableChange"
        rowKey="id"
      >
        <template #userInfo="{ record }">
          <div class="user-info">
            <a-avatar :src="record.avatar" :size="40"><UserOutlined /></a-avatar>
            <div class="user-details">
              <div class="username">{{ record.username }}</div>
              <div class="user-id">ID: {{ record.id }}</div>
            </div>
          </div>
        </template>
        <template #role="{ record }"><a-tag :color="record.role === 'admin' ? 'red' : 'blue'">{{ record.role === 'admin' ? '管理员' : '普通用户' }}</a-tag></template>
        <template #status="{ record }"><a-tag :color="record.status === 'active' ? 'green' : record.status === 'inactive' ? 'orange' : 'red'">{{ record.status === 'active' ? '正常' : record.status === 'inactive' ? '禁用' : '封禁' }}</a-tag></template>
        <template #action="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="handleEdit(record)"><EditOutlined />编辑</a-button>
            <a-dropdown>
              <a-button type="link" size="small">更多<DownOutlined /></a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item v-if="record.status !== 'active'" @click="handleStatusChange(record, 'active')">启用</a-menu-item>
                  <a-menu-item v-if="record.status !== 'inactive'" @click="handleStatusChange(record, 'inactive')">禁用</a-menu-item>
                  <a-menu-divider />
                  <a-menu-item danger @click="handleDelete(record)">删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style lang="scss" scoped>
.users { padding: 0; }
.search-card, .table-card { margin-bottom: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
.search-form { .search-actions { text-align: right; } }
.action-bar { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0; }
.user-info { display: flex; gap: 12px; align-items: center; }
.user-details { flex: 1; min-width: 0; }
.username { font-weight: 500; color: #262626; margin-bottom: 2px; }
.user-id { font-size: 12px; color: #8c8c8c; }
</style>
