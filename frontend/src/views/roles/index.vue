<template>
  <div class="roles">
    <!-- 搜索筛选区域 -->
    <a-card class="search-card" :bordered="false">
      <a-form :model="searchForm" class="search-form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-row :gutter="[16, 16]">
          <a-col :span="6">
            <a-form-item label="角色名称" labelAlign="right">
              <a-input
                v-model:value="searchForm.name"
                placeholder="请输入角色名称"
                @pressEnter="handleSearch"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="状态" labelAlign="right">
              <a-select
                v-model:value="searchForm.status"
                placeholder="请选择状态"
              >
                <a-select-option
                  v-for="option in statusOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" class="search-actions">
            <a-space>
              <a-button @click="handleReset">重置</a-button>
              <a-button type="primary" @click="handleSearch">
                <SearchOutlined />
                搜索
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </a-form>
    </a-card>

    <!-- 角色列表 -->
    <a-card class="table-card" :bordered="false">
      <!-- 操作按钮区域 -->
      <div class="action-bar">
        <a-space>
          <a-button type="primary" @click="handleAdd">
            <PlusOutlined />
            新增角色
          </a-button>
          <a-button 
            danger 
            :disabled="selectedRowKeys.length === 0"
            @click="handleBatchDelete"
          >
            <DeleteOutlined />
            批量删除
          </a-button>
          <a-button @click="loadData">
            <ReloadOutlined />
            刷新
          </a-button>
        </a-space>
      </div>
      
      <!-- 表格区域 -->
      <a-table
        :columns="columns"
        :dataSource="roleList"
        :loading="loading"
        :pagination="pagination"
        :rowSelection="{
          selectedRowKeys: selectedRowKeys,
          onChange: handleSelectionChange
        }"
        @change="handleTableChange"
        rowKey="id"
      >
        <!-- 角色信息列 -->
        <template #roleInfo="{ record }">
          <div class="role-info">
            <div class="role-name">{{ record.name }}</div>
            <div class="role-description">{{ record.description }}</div>
          </div>
        </template>

        <!-- 权限列 -->
        <template #permissions="{ record }">
          <a-tag 
            v-for="permission in record.permissions.slice(0, 2)"
            :key="permission"
            color="blue"
          >
            {{ permission }}
          </a-tag>
          <a-tag v-if="record.permissions.length > 2" color="default">
            +{{ record.permissions.length - 2 }}
          </a-tag>
        </template>

        <!-- 状态列 -->
        <template #status="{ record }">
          <a-tag 
            :color="record.status === 'active' ? 'green' : 'red'"
          >
            {{ record.status === 'active' ? '启用' : '禁用' }}
          </a-tag>
        </template>

        <!-- 操作列 -->
        <template #action="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="handleEdit(record)">
              <EditOutlined />
              编辑
            </a-button>
            <a-dropdown>
              <a-button type="link" size="small">
                更多
                <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item 
                    v-if="record.status !== 'active'"
                    @click="handleStatusChange(record, 'active')"
                  >
                    启用
                  </a-menu-item>
                  <a-menu-item 
                    v-if="record.status !== 'inactive'"
                    @click="handleStatusChange(record, 'inactive')"
                  >
                    禁用
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item 
                    danger
                    @click="handleDelete(record)"
                  >
                    删除
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

// 角色数据类型
interface RoleItem {
  id: number
  name: string
  description: string
  permissions: string[]
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
}

// 表格数据
const roleList = ref<RoleItem[]>([])
const loading = ref(false)
const selectedRowKeys = ref<number[]>([])

// 搜索表单
const searchForm = reactive({
  name: '',
  status: ''
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

// 表格列配置
const columns = [
  {
    title: '角色信息',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    slots: { customRender: 'roleInfo' }
  },
  {
    title: '权限',
    dataIndex: 'permissions',
    key: 'permissions',
    width: 200,
    slots: { customRender: 'permissions' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    slots: { customRender: 'action' }
  }
]

// 状态选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'inactive' }
]

// 模拟数据
const mockData: RoleItem[] = [
  {
    id: 1,
    name: '超级管理员',
    description: '拥有系统所有权限',
    permissions: ['用户管理', '角色管理', '商品管理', '系统设置'],
    status: 'active',
    createdAt: '2024-01-01 00:00:00',
    updatedAt: '2024-01-20 10:30:00'
  },
  {
    id: 2,
    name: '商品管理员',
    description: '负责商品和分类管理',
    permissions: ['商品管理', '分类管理'],
    status: 'active',
    createdAt: '2024-01-05 14:20:00',
    updatedAt: '2024-01-19 16:45:00'
  },
  {
    id: 3,
    name: '客服',
    description: '处理用户咨询和订单',
    permissions: ['用户查看', '订单查看'],
    status: 'inactive',
    createdAt: '2024-01-10 09:15:00',
    updatedAt: '2024-01-18 20:30:00'
  }
]

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    let filteredData = [...mockData]
    
    if (searchForm.name) {
      filteredData = filteredData.filter(item => 
        item.name.includes(searchForm.name)
      )
    }
    
    if (searchForm.status) {
      filteredData = filteredData.filter(item => item.status === searchForm.status)
    }
    
    const start = (pagination.current - 1) * pagination.pageSize
    const end = start + pagination.pageSize
    roleList.value = filteredData.slice(start, end)
    pagination.total = filteredData.length
  } catch (error) {
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadData()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    status: ''
  })
  pagination.current = 1
  loadData()
}

// 分页变化
const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadData()
}

// 选择变化
const handleSelectionChange = (keys: number[]) => {
  selectedRowKeys.value = keys
}

// 添加角色
const handleAdd = () => {
  message.info('添加角色')
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要删除的角色')
    return
  }
  message.info(`批量删除 ${selectedRowKeys.value.length} 个角色`)
}

// 编辑角色
const handleEdit = (record: RoleItem) => {
  message.info(`编辑角色: ${record.name}`)
}

// 删除角色
const handleDelete = (record: RoleItem) => {
  message.info(`删除角色: ${record.name}`)
}

// 状态切换
const handleStatusChange = (record: RoleItem, status: string) => {
  record.status = status as any
  message.success('状态更新成功')
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.roles {
  padding: 0;
}

.search-card,
.table-card {
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.search-form {
  .search-actions {
    text-align: right;
  }
}

.action-bar {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.role-info {
  .role-name {
    font-weight: 500;
    color: #262626;
    margin-bottom: 4px;
  }
  
  .role-description {
    font-size: 12px;
    color: #8c8c8c;
  }
}
</style>
