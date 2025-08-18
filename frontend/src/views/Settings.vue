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
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemAPI } from '@/api'

const isDark = ref(false)
const syncing = ref(false)
const checking = ref(false)
const healthStatus = ref(true)

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
