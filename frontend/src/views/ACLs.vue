<template>
  <div class="acls">
    <div class="page-header">
      <h2>访问控制规则</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加规则
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索源地址或目标地址"
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
        <!-- 批量操作按钮 -->
        <el-form-item v-if="selectedACLs.length > 0">
          <el-button type="danger" @click="batchDeleteACLs" :loading="batchDeleting">
            批量删除 ({{ selectedACLs.length }})
          </el-button>
          <el-button type="warning" @click="batchToggleACLs" :loading="batchToggling">
            批量切换状态 ({{ selectedACLs.length }})
          </el-button>
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
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
          <el-table-column type="index" label="序号" width="70" />
        <el-table-column label="节点" width="150">
          <template #default="{ row }">
            {{ getPeerName(row.peer_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="target" label="源地址" width="150" />
        <el-table-column prop="destination" label="目标地址" width="150">
          <template #default="{ row }">
            {{ row.destination || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="100">
          <template #default="{ row }">
            {{ row.port || '所有' }}
          </template>
        </el-table-column>
        <el-table-column label="协议" width="80">
          <template #default="{ row }">
            {{ row.protocol ? row.protocol : '所有' }}
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
        <el-table-column label="规则类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeType(row.rule_type)">
              {{ getRuleTypeText(row.rule_type) }}
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
      :title="isEdit ? '编辑访问控制规则' : '添加访问控制规则'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="aclForm"
        :rules="formRules"
        label-width="120px"
      >
        <!-- 规则类型选择 -->
        <el-form-item label="规则类型" prop="rule_type">
          <el-radio-group v-model="aclForm.rule_type" @change="onRuleTypeChange">
            <el-radio label="nat">NAT 规则（局域网访问 WireGuard 网络）</el-radio>
            <el-radio label="firewall">入站规则（控制节点访问权限）</el-radio>
          </el-radio-group>
          <div class="form-tip">
            <strong>NAT 规则：</strong>允许局域网设备通过路由访问 WireGuard 网络，源 IP 会被转换为宿主机 IP<br>
            <strong>入站规则：</strong>控制哪些设备可以访问 WireGuard 节点
          </div>
        </el-form-item>

        <!-- NAT 规则字段 -->
        <div v-if="aclForm.rule_type === 'nat'">
          <el-divider>NAT 规则配置</el-divider>
          
          <el-form-item label="源网段" prop="target" required>
            <el-input v-model="aclForm.target" placeholder="例如: 192.168.99.0/24（局域网网段）" />
            <div class="form-tip">允许访问 WireGuard 网络的局域网网段</div>
          </el-form-item>
          
          <el-form-item label="目标网段" prop="destination" required>
            <el-input v-model="aclForm.destination" placeholder="例如: 10.0.0.0/8（WireGuard 网络）" />
            <div class="form-tip">WireGuard 网络的目标网段</div>
          </el-form-item>
          
          <el-form-item label="源接口" prop="source_interface">
            <el-select v-model="aclForm.source_interface" placeholder="选择源接口" style="width: 100%">
              <el-option label="eth0（外网接口）" value="eth0" />
              <el-option label="wg0（WireGuard 接口）" value="wg0" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="目标接口" prop="destination_interface">
            <el-select v-model="aclForm.destination_interface" placeholder="选择目标接口" style="width: 100%">
              <el-option label="eth0（外网接口）" value="eth0" />
              <el-option label="wg0（WireGuard 接口）" value="wg0" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 入站规则字段 -->
        <div v-if="aclForm.rule_type === 'firewall'">
          <el-divider>入站规则配置</el-divider>
          
          <el-form-item label="目标节点" prop="peer_id">
            <el-select v-model="aclForm.peer_id" placeholder="选择目标节点" clearable style="width: 100%">
              <el-option label="所有节点" :value="null" />
              <el-option
                v-for="peer in peerOptions"
                :key="peer.id"
                :label="peer.remark || peer.peer_ip || peer.id"
                :value="peer.id"
              />
            </el-select>
            <div class="form-tip">选择要控制访问权限的 WireGuard 节点</div>
          </el-form-item>
          
          <el-form-item label="源 IP 地址" prop="target" required>
            <el-input v-model="aclForm.target" placeholder="例如: 192.168.99.10 或 192.168.99.0/24" />
            <div class="form-tip">允许访问的源 IP 地址或网段</div>
          </el-form-item>
          
          <el-form-item label="端口" prop="port">
            <el-select v-model="aclForm.port" placeholder="选择端口" style="width: 100%" filterable allow-create>
              <el-option label="所有端口" value="" />
              <el-option label="80 (HTTP)" value="80" />
              <el-option label="443 (HTTPS)" value="443" />
              <el-option label="22 (SSH)" value="22" />
            </el-select>
            <div class="form-tip">限制访问的端口，支持单个端口或范围（如 80-443）</div>
          </el-form-item>
          
          <el-form-item label="协议" prop="protocol">
            <el-select v-model="aclForm.protocol" placeholder="选择协议" style="width: 100%">
              <el-option label="所有协议" value="" />
              <el-option label="TCP" value="TCP" />
              <el-option label="UDP" value="UDP" />
              <el-option label="ICMP" value="ICMP" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 动作 -->
        <el-form-item label="动作" prop="action" required>
          <el-radio-group v-model="aclForm.action">
            <el-radio label="allow">允许</el-radio>
            <el-radio label="deny">拒绝</el-radio>
          </el-radio-group>
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
import { aclAPI, peerAPI, batchAPI } from '@/api'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const acls = ref([])
const selectedACLs = ref([])
const batchDeleting = ref(false)
const batchToggling = ref(false)

const filterForm = reactive({
  search: '',
  action: ''
})

const aclForm = reactive({
  id: null,
  rule_type: 'nat',  // 默认选择 NAT 规则
  peer_id: null,
  action: 'allow',
  target: '',
  destination: '',
  source_interface: 'eth0',
  destination_interface: 'wg0',
  port: '',
  protocol: ''
})

const formRules = {
  rule_type: [
    { required: true, message: '请选择规则类型', trigger: 'change' }
  ],
  peer_id: [
    // 节点现在是可选的，不再是必填项
  ],
  action: [
    { required: true, message: '请选择动作', trigger: 'change' }
  ],
  target: [
    { required: true, message: '请输入源地址', trigger: 'blur' }
  ],
  destination: [
    { required: true, message: '请输入目标网段', trigger: 'blur' }
  ],
  port: [
    // 端口现在是可选的
  ],
  protocol: [
    // 协议现在是可选的
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
  if (peer_id === -1) return "全局规则"
  const p = peerMap.value[peer_id]
  if (!p) return peer_id
  return p.remark || p.peer_ip || p.id
}

const getDirectionText = (direction) => {
  switch (direction) {
    case 'inbound': return '入口'
    case 'outbound': return '出口'
    case 'both': return '双向'
    default: return direction || '双向'
  }
}

const getDirectionType = (direction) => {
  switch (direction) {
    case 'inbound': return 'primary'
    case 'outbound': return 'warning'
    case 'both': return 'info'
    default: return 'info'
  }
}

const getRuleTypeText = (rule_type) => {
  switch (rule_type) {
    case 'firewall': return '入站规则'
    case 'nat': return 'NAT 规则'
    default: return rule_type || 'NAT 规则'
  }
}

const getRuleTypeType = (rule_type) => {
  switch (rule_type) {
    case 'firewall': return 'primary'
    case 'nat': return 'warning'
    default: return 'info'
  }
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
  aclForm.rule_type = acl.rule_type || 'nat'
  aclForm.peer_id = acl.peer_id
  aclForm.action = acl.action || 'allow'
  aclForm.target = acl.target || ''
  aclForm.destination = acl.destination || ''
  aclForm.source_interface = acl.source_interface || 'eth0'
  aclForm.destination_interface = acl.destination_interface || 'wg0'
  aclForm.port = acl.port || ''
  aclForm.protocol = acl.protocol || ''
}

const resetForm = () => {
  Object.assign(aclForm, {
    id: null,
    rule_type: 'nat',  // 默认选择 NAT 规则
    peer_id: null,
    action: 'allow',
    target: '',
    destination: '',
    source_interface: 'eth0',
    destination_interface: 'wg0',
    port: '',
    protocol: ''
  })
  formRef.value?.resetFields()
}

const submitForm = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      let response
      // 准备提交的数据
      const submitData = { ...aclForm }
      // 如果peer_id为null，设置为-1表示全局规则
      if (submitData.peer_id === null || submitData.peer_id === '') {
        submitData.peer_id = -1
      }
      
      if (isEdit.value) {
        response = await aclAPI.updateACL(aclForm.id, submitData)
        if (response.sync_success === false) {
          ElMessage.warning(response.msg || '防火墙 规则更新成功，但 WireGuard 同步失败')
        } else {
          ElMessage.success('防火墙 规则更新成功')
        }
      } else {
        response = await aclAPI.createACL(submitData)
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

const handleSelectionChange = (selection) => {
  selectedACLs.value = selection
}

// 批量删除选中的 ACLs
const batchDeleteACLs = async () => {
  if (selectedACLs.value.length === 0) return

  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedACLs.value.length} 个防火墙规则吗？此操作不可恢复。`,
    '批量删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    batchDeleting.value = true
    try {
      const aclIds = selectedACLs.value.map(acl => acl.id)
      const response = await batchAPI.batchDeleteACLs({ acl_ids: aclIds })
      ElMessage.success(response.msg)
      selectedACLs.value = []
      loadACLs()
    } catch (error) {
      console.error('批量删除ACL失败:', error)
    } finally {
      batchDeleting.value = false
    }
  })
}

// 批量切换选中 ACLs 的状态
const batchToggleACLs = async () => {
  if (selectedACLs.value.length === 0) return

  batchToggling.value = true
  try {
    const aclIds = selectedACLs.value.map(acl => acl.id)
    const response = await batchAPI.batchToggleACLs({ acl_ids: aclIds })
    ElMessage.success(response.msg)
    selectedACLs.value = []
    loadACLs()
  } catch (error) {
    console.error('批量切换ACL状态失败:', error)
  } finally {
    batchToggling.value = false
  }
}

const onRuleTypeChange = () => {
  // 重置不相关的字段
  if (aclForm.rule_type === 'nat') {
    aclForm.peer_id = null
    aclForm.port = ''
    aclForm.protocol = ''
  } else if (aclForm.rule_type === 'firewall') {
    aclForm.destination = ''
  }
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
