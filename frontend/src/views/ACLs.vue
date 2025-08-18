<template>
  <div class="acls">
    <div class="page-header">
      <h2>防火墙规则</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加 防火墙 规则
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索规则名称或源/目标"
            clearable
            @input="handleFilter"
          />
        </el-form-item>
        <el-form-item label="动作">
          <el-select v-model="filterForm.action" placeholder="全部动作" clearable @change="handleFilter">
            <el-option label="允许" value="allow" />
            <el-option label="拒绝" value="deny" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- ACL 列表 -->
    <el-card>
      <el-table 
        v-loading="loading" 
        :data="filteredACLs" 
        stripe
        style="width: 100%"
      >
          <el-table-column type="index" label="序号" width="70" />
        <el-table-column label="节点" width="180">
          <template #default="{ row }">
            {{ getPeerName(row.peer_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="target" label="目标地址" width="150" />
        <el-table-column prop="port" label="端口" width="120" />
        <el-table-column label="协议" width="80">
          <template #default="{ row }">
            {{ row.protocol === '*' ? '所有' : row.protocol }}
          </template>
        </el-table-column>
        <el-table-column label="动作" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.action === 'allow' ? 'success' : 'danger'">
              {{ scope.row.action === 'allow' ? '允许' : '拒绝' }}
            </el-tag>
          </template>
        </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                {{ scope.row.enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="showEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteACL(scope.row)">删除</el-button>
            <el-button
              size="small"
              :type="scope.row.enabled ? 'warning' : 'success'"
              @click="toggleACLStatus(scope.row)"
            >
              {{ scope.row.enabled ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 添加/编辑 ACL 对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑 防火墙 规则' : '添加 防火墙 规则'"
      width="700px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="aclForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="节点" prop="peer_id">
          <el-select v-model="aclForm.peer_id" placeholder="请选择节点" style="width: 100%">
            <el-option
              v-for="peer in peerOptions"
              :key="peer.id"
              :label="peer.remark || peer.peer_ip || peer.id"
              :value="peer.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标 IP" prop="target">
          <el-input v-model="aclForm.target" placeholder="例如: 192.168.1.0/24" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-select v-model="aclForm.port" placeholder="请选择端口" style="width: 100%" filterable allow-create>
            <el-option label="所有端口" value="*" />
            <el-option label="80 (HTTP)" value="80" />
            <el-option label="443 (HTTPS)" value="443" />
          </el-select>
          <div class="form-tip">支持单个端口、端口范围或选择"所有端口"，也可自定义输入</div>
        </el-form-item>
        <el-form-item label="协议" prop="protocol">
          <el-select v-model="aclForm.protocol" placeholder="请选择协议" style="width: 100%">
            <el-option label="所有" value="*" />
            <el-option label="TCP" value="TCP" />
            <el-option label="UDP" value="UDP" />
            <el-option label="ICMP" value="ICMP" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="动作" prop="action">
          <el-select v-model="aclForm.action" placeholder="选择动作" style="width: 100%">
            <el-option label="允许" value="allow" />
            <el-option label="拒绝" value="deny" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { aclAPI, peerAPI } from '@/api'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const acls = ref([])

const filterForm = reactive({
  search: '',
  action: ''
})

const aclForm = reactive({
  id: null,
  peer_id: null,
  action: 'allow',
  target: '',
  port: '',
  protocol: '*'
})

const formRules = {
  peer_id: [
    { required: true, message: '请选择 节点', trigger: 'change' }
  ],
  action: [
    { required: true, message: '请选择动作', trigger: 'change' }
  ],
  target: [
    { required: true, message: '请输入目标 IP', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ],
  protocol: [
    { required: true, message: '请选择协议', trigger: 'change' }
  ]
}
const peerOptions = ref([])
const peerMap = ref({})
const loadPeers = async () => {
  try {
    const res = await peerAPI.getPeers()
    peerOptions.value = Array.isArray(res) ? res : []
    // build a quick lookup map by id
    peerMap.value = {}
    peerOptions.value.forEach(p => {
      peerMap.value[p.id] = p
    })
  } catch (e) {
    peerOptions.value = []
  }
}

const getPeerName = (peer_id) => {
  const p = peerMap.value[peer_id]
  if (!p) return peer_id
  return p.remark || p.peer_ip || p.id
}

const filteredACLs = computed(() => {
  return acls.value.filter(acl => {
    const matchSearch = !filterForm.search || 
      acl.target.toLowerCase().includes(filterForm.search.toLowerCase())
    
    const matchAction = !filterForm.action || acl.action === filterForm.action
    
    return matchSearch && matchAction
  })
})

const loadACLs = async () => {
  loading.value = true
  try {
    acls.value = await aclAPI.getACLs()
  } catch (error) {
  console.error('加载防火墙规则失败:', error)
  } finally {
    loading.value = false
  }
}

const showAddDialog = async () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
  // only load peers when we don't already have them to avoid duplicate requests
  if (!peerOptions.value.length) {
    await loadPeers()
  }
}

const showEditDialog = (acl) => {
  isEdit.value = true
  dialogVisible.value = true
  aclForm.id = acl.id
  aclForm.peer_id = acl.peer_id
  aclForm.action = acl.action || 'allow'
  aclForm.target = acl.target || ''
  aclForm.port = acl.port || ''
  // backend returns '*' for all-protocols, map to '*' for select
  aclForm.protocol = (acl.protocol === '*' || !acl.protocol) ? '*' : acl.protocol || ''
}

const resetForm = () => {
  Object.assign(aclForm, {
    id: null,
    peer_id: null,
    action: 'allow',
    target: '',
  port: '',
  protocol: '*'
  })
  formRef.value?.resetFields()
}

const submitForm = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      let response
      if (isEdit.value) {
        response = await aclAPI.updateACL(aclForm.id, aclForm)
        if (response.sync_success === false) {
          ElMessage.warning(response.msg || '防火墙 规则更新成功，但 WireGuard 同步失败')
        } else {
          ElMessage.success('防火墙 规则更新成功')
        }
      } else {
        response = await aclAPI.createACL(aclForm)
        if (response.sync_success === false) {
          ElMessage.warning(response.msg || '防火墙 规则创建成功，但 WireGuard 同步失败')
        } else {
          ElMessage.success('防火墙 规则创建成功')
        }
      }
      
      dialogVisible.value = false
      loadACLs()
    } catch (error) {
      console.error('提交防火墙规则失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

const deleteACL = (acl) => {
  ElMessageBox.confirm(
    `确定要删除 防火墙 规则 (${getPeerName(acl.peer_id)} -> ${acl.target}) 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await aclAPI.deleteACL(acl.id)
      ElMessage.success('防火墙 规则删除成功')
      loadACLs()
    } catch (error) {
      console.error('删除防火墙规则失败:', error)
    }
  })
}

const toggleACLStatus = async (acl) => {
  try {
    if (acl.enabled) {
      await aclAPI.disableACL(acl.id)
      ElMessage.success('ACL 已禁用')
    } else {
      await aclAPI.enableACL(acl.id)
      ElMessage.success('ACL 已启用')
    }
    loadACLs()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

const handleFilter = () => {
  // 过滤逻辑在 computed 中处理
}

onMounted(() => {
  loadACLs()
  loadPeers()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.rule-preview {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.rule-preview code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #333;
}

.batch-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .batch-actions {
    left: 20px;
    right: 20px;
    transform: none;
  }
}

/* 暗黑主题 */
[data-theme="dark"] .page-header h2 {
  color: #e4e7ed;
}

[data-theme="dark"] .rule-preview {
  background-color: #2b2f33;
  border-color: #434343;
}

[data-theme="dark"] .rule-preview code {
  color: #e4e7ed;
}
</style>
