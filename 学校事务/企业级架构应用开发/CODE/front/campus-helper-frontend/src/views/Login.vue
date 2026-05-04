<template>
  <div class="login-container">
    <van-nav-bar title="欢迎登录" />
    
    <!-- Logo 和标题区域 -->
    <div class="logo-wrap">
      <van-icon name="smile-o" size="80" color="#1989fa" />
      <h2 class="app-title">校园帮办</h2>
    </div>

    <!-- 登录表单 -->
    <van-form @submit="onSubmit" class="login-form">
      <van-cell-group inset>
        <!-- 【升级1】标签和占位符改为“学号” -->
        <van-field
          v-model="studentId"
          name="studentId"
          label="学号"
          placeholder="请输入学号 (如: 20260001)"
          :rules="[{ required: true, message: '请填写学号' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      
      <div style="margin: 32px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          立即登录
        </van-button>
        
        <!-- 【升级2】美化后的注册跳转链接 -->
        <div class="register-link" @click="$router.push('/register')">
          还没有账号？点击这里去注册新同学
        </div>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios'

const router = useRouter()
const studentId = ref('') // 绑定学号
const password = ref('')
const loading = ref(false)

const onSubmit = async (values) => {
  loading.value = true
  try {
    // 【升级3】为了不改动后端 Controller，这里把 key 依然写成 username，但传的是真实的学号
    const res = await axios.post('http://localhost:8080/api/user/login', {
      username: values.studentId,
      password: values.password
    })

    if (res.data && res.data.code === 200) {
      showSuccessToast('登录成功')
      
      // 1. 将后端返回的 token 永久存入浏览器的 localStorage
      localStorage.setItem('token', res.data.data.token)
      
      // 2. 存下后端的 nickname (后端放在了 username 字段里返回) 和 userId
      // Mine.vue 页面会自动去 localStorage 拿这两个值展示
      localStorage.setItem('username', res.data.data.username)
      localStorage.setItem('userId', res.data.data.userId)

      // 3. 登录成功后，编程跳转到任务大厅
      router.push('/hall')
    }
  } catch (error) {
    console.error('登录失败:', error)
    showFailToast(error.response?.data?.error || '学号或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}
.logo-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0 40px;
}
.app-title {
  margin-top: 16px;
  color: #323233;
  font-size: 24px;
  font-weight: bold;
  letter-spacing: 2px;
}
.login-form {
  margin-top: 20px;
}
.register-link {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
  letter-spacing: 1px;
}
</style>