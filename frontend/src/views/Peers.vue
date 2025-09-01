import { peerAPI, batchAPI } from '@/api'
<template>
  <div class="peers">
    <div class="page-header">
      <h2>节点管理</h2>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
          添加 节点
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索节点名称或 IP"
            clearable
            @input="handleFilter"
          />
        </el-form-item>
    <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable @change="handleFilter">
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <!-- 批量操作按钮 -->
        <el-form-item v-if="selectedPeers.length > 0">
          <el-button type="danger" @click="batchDeletePeers" :loading="batchDeleting">
            批量删除 ({{ selectedPeers.length }})
          </el-button>
          <el-button type="warning" @click="batchTogglePeers" :loading="batchToggling">
            批量切换状态 ({{ selectedPeers.length }})
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
  <!-- 节点 列表 -->
    <el-card>
      <el-table 
        v-loading="loading" 
        :data="filteredPeers" 
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="remark" label="名称" />
        <el-table-column prop="public_key" label="公钥" show-overflow-tooltip />
        <el-table-column prop="allowed_ips" label="允许的 IP" />
        <el-table-column prop="endpoint" label="端点" />
        <el-table-column label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.status ? 'success' : 'danger'">
              {{ scope.row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="showEditDialog(scope.row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              :type="scope.row.status ? 'warning' : 'success'"
              @click="togglePeer(scope.row)"
            >
              {{ scope.row.status ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deletePeer(scope.row)"
            >
              删除
            </el-button>
            <el-button size="small" @click="downloadConfig(scope.row)">
              下载配置
            </el-button>
            <el-button size="small" @click="showQRCode(scope.row)">
              二维码
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
  <!-- 添加/编辑 节点 对话框 -->
    <el-dialog
      v-model="dialogVisible"
  :title="isEdit ? '编辑 节点' : '添加 节点'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="peerForm"
        :rules="formRules"
        label-width="100px"
      >
          <el-form-item label="名称/备注" prop="remark">
          <el-input v-model="peerForm.remark" placeholder="输入节点名称或备注" />
        </el-form-item>
        
        <el-form-item label="公钥" prop="public_key">
          <el-input
            v-model="peerForm.public_key"
            placeholder="输入或生成公钥"
            type="textarea"
            :rows="3"
          />
          <div style="margin-top: 10px;">
            <el-button size="small" @click="generateKeyPair">
              生成密钥对
            </el-button>
            <el-button size="small" type="info" @click="showPrivateKey" v-if="generatedPrivateKey">
              查看私钥
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="允许的 IP" prop="allowed_ips">
              <el-input
                v-model="peerForm.allowed_ips"
                placeholder="例如: 0.0.0.0/0，支持自定义，首项始终为 节点 IP/32"
              />
              <div class="form-tip">
                    AllowedIPs 首项始终为 节点 IP/32，后续可自定义追加，支持 CIDR 格式，多个 IP 用逗号分隔
                  </div>
        </el-form-item>

          <el-form-item label="节点 IP" prop="peer_ip">
            <el-input
              v-model="peerForm.peer_ip"
              readonly
              placeholder="自动分配，唯一不可更改"
            />
            <div class="form-tip">
                由后端自动分配，唯一且不可更改
              </div>
          </el-form-item>
        
        <el-form-item label="端点">
          <el-input
            v-model="peerForm.endpoint"
            placeholder="例如: example.com:51820 (可选)"
          />
        </el-form-item>

        <el-form-item label="Keepalive (秒)" prop="keepalive">
          <el-input-number
            v-model="peerForm.keepalive"
            :min="30"
            :max="120"
            :step="1"
            placeholder="默认 30，最大 120"
          />
          <div class="form-tip">
            WireGuard 保活间隔，建议 30-120 秒
          </div>
        </el-form-item>
        
        
        <el-form-item label="状态">
          <el-switch
            v-model="peerForm.status"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="备注">
            <el-input
            v-model="peerForm.remark"
            type="textarea"
            :rows="3"
            placeholder="输入备注信息 (可选)"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 私钥显示对话框 -->
    <el-dialog
      v-model="privateKeyVisible"
      title="生成的私钥"
      width="500px"
    >
      <el-alert
        title="请妥善保存私钥"
        description="私钥只显示一次，请立即复制并保存到安全位置"
        type="warning"
        show-icon
        :closable="false"
      />
      <div style="margin-top: 20px;">
        <el-input
          :value="generatedPrivateKey"
          type="textarea"
          :rows="4"
          readonly
        />
        <div style="margin-top: 10px; text-align: right;">
          <el-button @click="copyPrivateKey">复制私钥</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 二维码对话框 -->
    <el-dialog
      v-model="qrCodeDialogVisible"
      title="客户端配置二维码"
      width="350px"
    >
      <div style="text-align:center">
        <img v-if="qrCodeImageUrl" :src="qrCodeImageUrl" alt="二维码" style="max-width: 300px;" />
        <div v-else>二维码加载中...</div>
      </div>
      <template #footer>
        <el-button @click="qrCodeDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { peerAPI } from '@/api'

const loading = ref(false)
const dialogVisible = ref(false)
const privateKeyVisible = ref(false)
const qrCodeDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const peers = ref([])
const generatedPrivateKey = ref('')
const qrCodeImageUrl = ref('')
const selectedPeers = ref([])
const batchDeleting = ref(false)
const batchToggling = ref(false)

const filterForm = reactive({
  search: '',
  status: ''
})

const peerForm = reactive({
  id: null,
  remark: '',
  public_key: '',
  allowed_ips: '',
  peer_ip: '',
  endpoint: '',
  keepalive: 30,
  status: true
})

const formRules = {
  remark: [
    { required: true, message: '请输入节点名称或备注', trigger: 'blur' }
  ],
  public_key: [
    { required: true, message: '请输入或生成公钥', trigger: 'blur' }
  ],
  allowed_ips: [
    { required: true, message: '请输入允许的 IP', trigger: 'blur' }
  ]
}

const filteredPeers = computed(() => {
  return peers.value.filter(peer => {
    const matchSearch = !filterForm.search || 
      (peer.remark && peer.remark.toLowerCase().includes(filterForm.search.toLowerCase())) ||
      peer.allowed_ips.toLowerCase().includes(filterForm.search.toLowerCase())
    
    const matchStatus = !filterForm.status || 
      (filterForm.status === 'enabled' && peer.status) ||
      (filterForm.status === 'disabled' && !peer.status)
    
    return matchSearch && matchStatus
  })
})

const loadPeers = async () => {
  loading.value = true
  try {
    peers.value = await peerAPI.getPeers()
  } catch (error) {
    console.error('加载节点列表失败:', error)
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
  // 弹窗时自动获取 peer_ip 并设置 allowed_ips 默认值
  peerAPI.getAvailablePeerIP().then(res => {
    peerForm.peer_ip = res.peer_ip || ''
    peerForm.allowed_ips = res.peer_ip ? `${res.peer_ip}/32` : ''
  }).catch(() => {
    peerForm.peer_ip = ''
    peerForm.allowed_ips = ''
  })
}

const showEditDialog = (peer) => {
  isEdit.value = true
  dialogVisible.value = true
  peerForm.id = peer.id
  peerForm.remark = peer.remark || ''
  peerForm.public_key = peer.public_key || ''
  peerForm.peer_ip = peer.peer_ip || ''
  // 编辑时 allowed_ips 默认首项为 peer_ip/32
  if (peer.peer_ip) {
    const custom_ips = peer.allowed_ips ? peer.allowed_ips.split(',').map(ip => ip.trim()).filter(ip => ip !== `${peer.peer_ip}/32`) : [];
    peerForm.allowed_ips = [`${peer.peer_ip}/32`, ...custom_ips].join(', ');
  } else {
    peerForm.allowed_ips = peer.allowed_ips || '';
  }
  peerForm.endpoint = peer.endpoint || ''
  peerForm.keepalive = typeof peer.keepalive === 'number' ? peer.keepalive : 30
  peerForm.status = typeof peer.status === 'boolean' ? peer.status : true
}

const resetForm = () => {
  Object.assign(peerForm, {
    id: null,
    remark: '',
    public_key: '',
    allowed_ips: '',
    peer_ip: '',
    endpoint: '',
    keepalive: 30,
    status: true
  })
  generatedPrivateKey.value = ''
  formRef.value?.resetFields()
}

const generateKeyPair = async () => {
  try {
    const response = await peerAPI.generateKey()
    peerForm.public_key = response.public_key
    generatedPrivateKey.value = response.private_key
    ElMessage.success('密钥对生成成功')
  } catch (error) {
  console.error('生成密钥对失败:', error)
  }
}

const showPrivateKey = () => {
  privateKeyVisible.value = true
}

const copyPrivateKey = () => {
  navigator.clipboard.writeText(generatedPrivateKey.value).then(() => {
    ElMessage.success('私钥已复制到剪贴板')
  })
}

const downloadConfig = async (peer) => {
  try {
    const blob = await peerAPI.downloadPeerConfig(peer.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `peer_${peer.id}_config.conf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('配置文件已下载')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const showQRCode = async (peer) => {
  try {
    const blob = await peerAPI.getPeerConfigQRCode(peer.id)
    qrCodeImageUrl.value = window.URL.createObjectURL(blob)
    qrCodeDialogVisible.value = true
  } catch (error) {
    ElMessage.error('二维码获取失败')
  }
}

const submitForm = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      let response
        if (isEdit.value) {
        response = await peerAPI.updatePeer(peerForm.id, peerForm)
        if (response.sync_success === false) {
          ElMessage.warning(response.msg || '节点更新成功，但 WireGuard 同步失败')
        } else {
          ElMessage.success('节点更新成功')
        }
      } else {
        response = await peerAPI.createPeer(peerForm)
        if (response.sync_success === false) {
          ElMessage.warning(response.msg || '节点创建成功，但 WireGuard 同步失败')
        } else {
          ElMessage.success('节点创建成功')
        }
      }
      
      dialogVisible.value = false
      loadPeers()
    } catch (error) {
      console.error('提交节点失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

const togglePeer = async (peer) => {
  try {
    const response = await peerAPI.togglePeer(peer.id)
    ElMessage.success(`节点 ${response.status ? '启用' : '禁用'} 成功`)
    loadPeers()
  } catch (error) {
    console.error('切换节点状态失败:', error)
  }
}

const deletePeer = (peer) => {
  ElMessageBox.confirm(
    `确定要删除 节点 "${peer.remark || peer.id}" 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await peerAPI.deletePeer(peer.id)
  ElMessage.success('节点删除成功')
      loadPeers()
    } catch (error) {
  console.error('删除节点失败:', error)
    }
  })
}

const handleFilter = () => {
  // 过滤逻辑在 computed 中处理
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleSelectionChange = (selection) => {
  selectedPeers.value = selection
}

const batchDeletePeers = async () => {
  if (selectedPeers.value.length === 0) return

  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedPeers.value.length} 个节点吗？此操作不可恢复。`,
    '批量删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    batchDeleting.value = true
    try {
      const peerIds = selectedPeers.value.map(peer => peer.id)
      const response = await batchAPI.batchDeletePeers({ peer_ids: peerIds })
      ElMessage.success(response.msg)
      selectedPeers.value = []
      loadPeers()
    } catch (error) {
      console.error('批量删除节点失败:', error)
    } finally {
      batchDeleting.value = false
    }
  })
}

const batchTogglePeers = async () => {
  if (selectedPeers.value.length === 0) return

  batchToggling.value = true
  try {
    const peerIds = selectedPeers.value.map(peer => peer.id)
    const response = await batchAPI.batchTogglePeers({ peer_ids: peerIds })
    ElMessage.success(response.msg)
    selectedPeers.value = []
    loadPeers()
  } catch (error) {
    console.error('批量切换节点状态失败:', error)
  } finally {
    batchToggling.value = false
  }
}

onMounted(() => {
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

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}

/* 暗黑主题 */
[data-theme="dark"] .page-header h2 {
  color: #e4e7ed;
}
</style>
