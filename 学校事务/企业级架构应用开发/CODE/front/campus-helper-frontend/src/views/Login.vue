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
        <van-field
          v-model="username"
          name="username"
          label="账号"
          placeholder="测试用例: zhangsan 或 lisi"
          :rules="[{ required: true, message: '请填写账号' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="测试用例: 123456"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      
      <div style="margin: 32px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          立即登录
        </van-button>
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
const username = ref('')
const password = ref('')
const loading = ref(false)

const onSubmit = async (values) => {
  loading.value = true
  try {
    // 1. 发送账号密码给后端，请求换取门票
    const res = await axios.post('http://localhost:8080/api/user/login', {
      username: values.username,
      password: values.password
    })

    if (res.data && res.data.code === 200) {
      showSuccessToast('登录成功')
      
      // 2. 【核心动作：存门票】将后端返回的 token 永久存入浏览器的 localStorage
      localStorage.setItem('token', res.data.data.token)
      
      // 顺便把用户名和用户ID也存下来，方便其他页面（如“我的”页面）展示
      localStorage.setItem('username', res.data.data.username)
      localStorage.setItem('userId', res.data.data.userId)

      // 3. 登录成功后，编程跳转到任务大厅
      router.push('/hall')
    }
  } catch (error) {
    console.error('登录失败:', error)
    showFailToast(error.response?.data?.error || '账号或密码错误')
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
</style>