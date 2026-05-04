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
        
        <!-- 使用自定义函数进行跳转，最稳妥的写法 -->
        <div class="register-link" @click="goToRegister">
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

// 【新增】：跳转到注册页的函数
const goToRegister = () => {
  console.log('准备跳转到注册页...') // 如果点下去没反应，按 F12 看看控制台有没有打印这句话
  router.push('/register')
}

// 提交登录逻辑
const onSubmit = async (values) => {
  loading.value = true
  try {
    // 传给后端的 key 依然是 username，但值是真实的学号
    const res = await axios.post('http://localhost:8080/api/user/login', {
      username: values.studentId,
      password: values.password
    })

    if (res.data && res.data.code === 200) {
      showSuccessToast('登录成功')
      
      // 1. 将后端返回的 token 永久存入浏览器的 localStorage
      localStorage.setItem('token', res.data.data.token)
      
      // 2. 存下后端的 nickname (后端放在了 username 字段里返回) 和 userId
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