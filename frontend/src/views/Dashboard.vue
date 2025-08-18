<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon color="#409eff" size="40"><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.peerCount }}</div>
              <div class="stat-label">节点 总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon color="#67c23a" size="40"><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.aclCount }}</div>
              <div class="stat-label">防火墙 规则</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon color="#e6a23c" size="40"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.userCount }}</div>
              <div class="stat-label">用户数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon color="#f56c6c" size="40"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.onlineNodes }}</div>
              <div class="stat-label">活跃节点</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 系统状态 -->
    <el-row :gutter="20">      
      <el-col :md="12">
        <el-card class="equal-height-card">
          <template #header>
            <div class="card-header">
              <span>系统资源监控</span>
            </div>
          </template>

          <div class="system-resources">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="CPU 使用率">
                <el-progress :percentage="sysResources.cpu_percent" :color="getLoadColor(sysResources.cpu_percent)" />
              </el-descriptions-item>
              <el-descriptions-item label="内存 使用率">
                <div>{{ (sysResources.memory.percent || 0) }}% · {{ (sysResources.memory.used / 1024 / 1024).toFixed(1) }}MB / {{ (sysResources.memory.total / 1024 / 1024).toFixed(1) }}MB</div>
                <el-progress :percentage="sysResources.memory.percent" />
              </el-descriptions-item>
              <el-descriptions-item label="磁盘 使用率">
                <div>{{ (sysResources.disk.percent || 0) }}% · {{ (sysResources.disk.used / 1024 / 1024 /1024).toFixed(2) }}GB / {{ (sysResources.disk.total / 1024 / 1024 /1024).toFixed(2) }}GB</div>
                <el-progress :percentage="sysResources.disk.percent" />
              </el-descriptions-item>
              <el-descriptions-item label="网络 速率">
                <div>上行: {{ (sysResources.network.bytes_sent_per_s / 1024).toFixed(1) }} KB/s · 下行: {{ (sysResources.network.bytes_recv_per_s / 1024).toFixed(1) }} KB/s</div>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      <el-col :md="12">
        <el-card class="equal-height-card">
          <template #header>
            <span>最近活动</span>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.timestamp"
              :type="activity.type"
            >
              {{ activity.message }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速操作 -->
    <el-card class="quick-actions-card">
      <template #header>
        <span>快速操作</span>
      </template>
      
      <div class="quick-actions">
        <el-button type="primary" @click="$router.push('/nodes')">
          <el-icon><Plus /></el-icon>
          添加 节点
        </el-button>
        <el-button type="success" @click="$router.push('/firewall-rules')">
          <el-icon><Shield /></el-icon>
          创建 防火墙 规则
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { peerAPI, aclAPI, userAPI, systemAPI, systemStatsAPI, activitiesAPI } from '@/api'

const stats = reactive({
  peerCount: 0,
  aclCount: 0,
  userCount: 0,
  onlineNodes: 0
})

const systemStatus = reactive({
  wireguard: true,
  database: true,
  sync: true,
  load: 45
})

const sysResources = reactive({
  cpu_percent: 0,
  memory: { total: 0, used: 0, percent: 0 },
  disk: { total: 0, used: 0, percent: 0 },
  network: { bytes_sent_per_s: 0, bytes_recv_per_s: 0 }
})

let statsTimer = null
let activitiesTimer = null

const recentActivities = ref([])

const loadRecentActivities = async () => {
  try {
    const res = await activitiesAPI.getRecent(20)
    const data = res.data || res
    recentActivities.value = data
  } catch (error) {
    console.error('获取最近活动失败:', error)
  }
}

const loadStats = async () => {
  try {
    const [peers, acls, users, onlineNodesRes] = await Promise.all([
      peerAPI.getPeers(),
      aclAPI.getACLs(),
      userAPI.getUsers(),
      peerAPI.getOnlineNodesCount()
    ])
    stats.peerCount = peers.length
    stats.aclCount = acls.length
    stats.userCount = users.length
    stats.onlineNodes = onlineNodesRes.wg_online_nodes_count || 0
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const refreshStatus = async () => {
  try {
    await systemAPI.health()
    systemStatus.database = true
    ElMessage.success('状态刷新成功')
  } catch (error) {
    systemStatus.database = false
    console.error('刷新状态失败:', error)
  }
}

const loadSystemResources = async () => {
  try {
    const res = await systemStatsAPI.stats()
    const data = res.data || res
    sysResources.cpu_percent = data.cpu_percent
    sysResources.memory = data.memory || sysResources.memory
    sysResources.disk = data.disk || sysResources.disk
    sysResources.network = data.network || sysResources.network
  } catch (error) {
    console.error('获取系统资源失败:', error)
  }
}

const getLoadColor = (load) => {
  if (load < 50) return '#67c23a'
  if (load < 80) return '#e6a23c'
  return '#f56c6c'
}

const exportConfig = () => {
  ElMessage.info('配置导出功能开发中...')
}

onMounted(() => {
  loadStats()
  // 立即加载一次系统资源并启动轮询（每5秒）
  loadSystemResources()
  statsTimer = setInterval(loadSystemResources, 5000)
  // 加载最近活动并轮询（每5秒）
  loadRecentActivities()
  activitiesTimer = setInterval(loadRecentActivities, 5000)
})

onUnmounted(() => {
  if (statsTimer) clearInterval(statsTimer)
  if (activitiesTimer) clearInterval(activitiesTimer)
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
  color: #303133;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.system-status {
  margin-top: 10px;
}

.equal-height-card {
  height: 100%;
}

.equal-height-card .el-card__body {
  min-height: 300px;
}

.quick-actions-card {
  margin-top: 20px;
}

.quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 120px;
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }
  
  .quick-actions .el-button {
    width: 100%;
  }
}

/* 暗黑主题 */
[data-theme="dark"] .dashboard h2 {
  color: #e4e7ed;
}

[data-theme="dark"] .stat-number {
  color: #e4e7ed;
}

/* 确保最近活动时间线在任何主题下都可见 */
.el-timeline-item,
.el-timeline-item__content {
  color: #303133 !important;
}
.el-timeline-item__dot {
  background-color: #409eff !important;
}
</style>
