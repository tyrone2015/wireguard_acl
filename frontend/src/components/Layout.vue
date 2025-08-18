<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="header-left">
        <h3>WireGuard 防火墙规则平台</h3>
        <!-- 顶部导航菜单 -->
        <el-menu
          :default-active="$route.path"
          mode="horizontal"
          router
          class="top-nav-menu"
        >
          <template v-for="menu in sidebarMenus" :key="menu.path">
            <el-menu-item :index="'/' + menu.path">
              <el-icon :style="getIconStyle(menu.meta.icon)">
                <component :is="Icons[menu.meta.icon]" />
              </el-icon>
              <span>{{ menu.meta.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </div>
      
      <div class="header-right">
        <el-button
          circle
          :icon="isDark ? 'Sunny' : 'Moon'"
          @click="toggleTheme"
        />
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ username }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    
    <el-main class="main-content">
      <router-view />
    </el-main>
    
    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="changePasswordVisible"
      title="修改密码"
      width="400px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="changePasswordVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authAPI } from '@/api'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '')
const isDark = ref(false)
const changePasswordVisible = ref(false)
const passwordFormRef = ref()
const passwordLoading = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 获取侧边栏菜单项（从路由 children 动态获取）
const sidebarMenus = computed(() => {
  const route = router.options.routes.find(r => r.path === '/')
  return route && route.children ? route.children : []
})

// 图标样式映射，可根据需要自定义颜色
const iconColorMap = {
  Odometer: '#409EFF',
  Share: '#67C23A', 
  Shield: '#E6A23C',
  Setting: '#F56C6C'
}

const getIconStyle = (icon) => {
  return `color:${iconColorMap[icon] || '#409EFF'};font-size:22px;`
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const handleCommand = (command) => {
  if (command === 'changePassword') {
    changePasswordVisible.value = true
  } else if (command === 'logout') {
    handleLogout()
  }
}

const handleChangePassword = () => {
  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      await authAPI.changePassword({
        old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword
      })
      
      ElMessage.success('密码修改成功')
      changePasswordVisible.value = false
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    } catch (error) {
  console.error('修改密码失败:', error)
    } finally {
      passwordLoading.value = false
    }
  })
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
    ElMessage.success('已退出登录')
  })
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
.layout-container {
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #e6e6e6;
  background-color: #fff;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 30px;
  flex: 1;
  min-width: 0; /* 允许flex项收缩 */
}

.header-left h3 {
  color: #303133;
  margin: 0;
  white-space: nowrap;
  flex-shrink: 0; /* 标题不收缩 */
}

.top-nav-menu {
  border-bottom: none;
  background-color: transparent;
  flex: 1;
  max-width: none;
}

.top-nav-menu .el-menu-item {
  height: 60px;
  line-height: 60px;
  border-bottom: 2px solid transparent;
  padding: 0 20px;
  white-space: nowrap;
}

.top-nav-menu .el-menu-item:hover {
  background-color: transparent;
  color: #409eff;
  border-bottom-color: #409eff;
}

.top-nav-menu .el-menu-item.is-active {
  background-color: transparent;
  color: #409eff;
  border-bottom-color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.main-content {
  padding: 20px;
  background-color: #f5f7fa;
}

/* 暗黑主题 */
[data-theme="dark"] .header {
  background-color: #2b2f33;
  border-bottom-color: #434343;
}

[data-theme="dark"] .header-left h3 {
  color: #e4e7ed;
}

[data-theme="dark"] .top-nav-menu .el-menu-item:hover {
  color: #409eff;
  background-color: transparent;
}

[data-theme="dark"] .top-nav-menu .el-menu-item.is-active {
  color: #409eff;
  background-color: transparent;
}

[data-theme="dark"] .user-dropdown:hover {
  background-color: #434343;
}

[data-theme="dark"] .main-content {
  background-color: #1d1e1f;
}

/* 响应式布局 */
@media (max-width: 1024px) {
  .header-left h3 {
    font-size: 16px;
  }
  
  .header-left {
    gap: 20px;
  }
  
  .top-nav-menu .el-menu-item {
    padding: 0 15px;
  }
  
  .top-nav-menu .el-menu-item span {
    font-size: 14px;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    height: auto;
    padding: 10px 20px;
  }
  
  .header-left {
    width: 100%;
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .top-nav-menu {
    width: 100%;
    justify-content: center;
  }
  
  .top-nav-menu .el-menu-item {
    padding: 0 15px;
    height: 50px;
    line-height: 50px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
    margin-top: 10px;
  }
}
</style>
