<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>WireGuard 防火墙规则平台</h2>
          <p>请输入您的登录凭据</p>
        </div>
      </template>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="theme-toggle">
        <el-button
          circle
          :icon="isDark ? 'Sunny' : 'Moon'"
          @click="toggleTheme"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'

const router = useRouter()
const loginFormRef = ref()
const loading = ref(false)
const isDark = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const handleLogin = () => {
  loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('username', loginForm.username)
      formData.append('password', loginForm.password)
      
      const response = await authAPI.login(formData)
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('username', loginForm.username)
      
      ElMessage.success('登录成功')
      router.push('/')
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      loading.value = false
    }
  })
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
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
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  position: relative;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.card-header p {
  color: #909399;
  font-size: 14px;
}

.theme-toggle {
  position: absolute;
  top: 20px;
  right: 20px;
}

/* 暗黑主题 */
[data-theme="dark"] .login-container {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
}

[data-theme="dark"] .card-header h2 {
  color: #e4e7ed;
}

[data-theme="dark"] .card-header p {
  color: #a8abb2;
}
</style>
