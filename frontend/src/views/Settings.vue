<template>
  <div class="settings">
    <h2>系统设置</h2>
    <el-card>
      <el-form label-width="120px">
        <el-form-item label="主题切换">
          <el-switch
            v-model="isDark"
            active-text="暗黑模式"
            inactive-text="明亮模式"
            @change="toggleTheme"
          />
        </el-form-item>
        <el-form-item label="WireGuard 配置同步">
          <el-button type="primary" @click="syncConfig" :loading="syncing">
            同步配置
          </el-button>
        </el-form-item>
        <el-form-item label="系统健康检查">
          <el-button type="info" @click="checkHealth" :loading="checking">
            检查健康
          </el-button>
          <el-tag :type="healthStatus ? 'success' : 'danger'" style="margin-left: 10px;">
            {{ healthStatus ? '正常' : '异常' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="配置备份">
          <el-button type="success" @click="exportConfig" :loading="exporting">
            导出配置
          </el-button>
          <el-button type="info" @click="importConfig" :loading="importing">
            导入配置
          </el-button>
        </el-form-item>
        <el-form-item label="备份状态">
          <el-button type="default" @click="checkBackupStatus" :loading="checkingBackup">
            查看备份状态
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemAPI, backupAPI } from '@/api'

const isDark = ref(false)
const syncing = ref(false)
const checking = ref(false)
const healthStatus = ref(true)
const exporting = ref(false)
const importing = ref(false)
const checkingBackup = ref(false)

const toggleTheme = () => {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const syncConfig = async () => {
  syncing.value = true
  ElMessage.info('配置同步功能开发中...')
  setTimeout(() => {
    syncing.value = false
    ElMessage.success('配置同步完成（模拟）')
  }, 1500)
}

const checkHealth = async () => {
  checking.value = true
  try {
    await systemAPI.health()
    healthStatus.value = true
    ElMessage.success('系统健康')
  } catch (error) {
    healthStatus.value = false
    ElMessage.error('系统异常')
  } finally {
    checking.value = false
  }
}

const exportConfig = async () => {
  exporting.value = true
  try {
    const config = await backupAPI.exportConfig()
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `wireguard_config_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('配置导出成功')
  } catch (error) {
    ElMessage.error('配置导出失败')
  } finally {
    exporting.value = false
  }
}

const importConfig = async () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    importing.value = true
    try {
      const text = await file.text()
      const config = JSON.parse(text)
      const response = await backupAPI.importConfig(config)
      ElMessage.success(response.msg)
    } catch (error) {
      ElMessage.error('配置导入失败')
    } finally {
      importing.value = false
    }
  }
  input.click()
}

const checkBackupStatus = async () => {
  checkingBackup.value = true
  try {
    const status = await backupAPI.getBackupStatus()
    ElMessage.info(`节点数量: ${status.peer_count}, 规则数量: ${status.acl_count}`)
  } catch (error) {
    ElMessage.error('获取备份状态失败')
  } finally {
    checkingBackup.value = false
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})
</script>

<style scoped>
.settings {
  max-width: 600px;
  margin: 0 auto;
}

.settings h2 {
  margin-bottom: 20px;
  color: #303133;
}

@media (max-width: 768px) {
  .settings {
    max-width: 100%;
    padding: 0 10px;
  }
}

/* 暗黑主题 */
[data-theme="dark"] .settings h2 {
  color: #e4e7ed;
}
</style>
