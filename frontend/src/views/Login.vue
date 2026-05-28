<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="login-header">
        <h2>AI 踝上截骨规划系统</h2>
        <p>Ankle Surgery Planning System</p>
      </div>
      <el-form label-position="top">
        <el-form-item label="登录账号"><el-input v-model="form.username" placeholder="输入 admin" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" placeholder="输入 123456" show-password /></el-form-item>
        <el-button type="primary" class="login-btn" @click="handleLogin">登 录 系 统</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = ref({ username: 'admin', password: '123456' })

const handleLogin = () => {
  if (form.value.username === 'admin' && form.value.password === '123456') {
    ElMessage.success('登录成功')
    router.push('/dashboard/workspace')
  } else {
    ElMessage.error('账号或密码错误')
  }
}
</script>

<style scoped>
.login-container { height: 100vh; display: flex; justify-content: center; align-items: center; background: linear-gradient(135deg, #1890ff 0%, #e6f7ff 100%); }
.login-card { width: 400px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); padding: 20px; }
.login-header { text-align: center; margin-bottom: 30px; }
.login-btn { width: 100%; font-size: 16px; padding: 12px 0; }
</style>