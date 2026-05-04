<template>
  <div class="register-container">
    <!-- 顶部导航：带返回按钮 -->
    <van-nav-bar 
      title="注册校园帮办" 
      left-arrow 
      @click-left="$router.back()" 
    />
    
    <div class="logo-wrap">
      <van-icon name="friends-o" size="80" color="#1989fa" />
      <h2 class="app-title">欢迎新同学</h2>
    </div>

    <!-- 注册表单 -->
    <van-form @submit="onSubmit" class="register-form">
      <van-cell-group inset>
        <van-field
          v-model="formData.studentId"
          name="studentId"
          label="学号"
          placeholder="请输入学号 (如: 20260002)"
          :rules="[{ required: true, message: '请填写学号' }]"
        />
        <van-field
          v-model="formData.nickname"
          name="nickname"
          label="昵称"
          placeholder="起个好听的名字吧"
          :rules="[{ required: true, message: '请填写昵称' }]"
        />
        <van-field
          v-model="formData.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
        <van-field
          v-model="formData.confirmPassword"
          type="password"
          name="confirmPassword"
          label="确认密码"
          placeholder="请再次输入密码"
          :rules="[
            { required: true, message: '请确认密码' },
            { validator: validatePassword, message: '两次输入的密码不一致' }
          ]"
        />
      </van-cell-group>
      
      <div style="margin: 32px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          立即注册
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)

// 使用 reactive 统一管理表单数据
const formData = reactive({
  studentId: '',
  nickname: '',
  password: '',
  confirmPassword: ''
})

// 自定义校验函数：检查两次密码是否一致
const validatePassword = (val) => {
  return val === formData.password
}

// 提交注册逻辑
const onSubmit = async () => {
  loading.value = true
  try {
    // 呼叫后端的注册接口
    const res = await axios.post('http://localhost:8080/api/user/register', {
      studentId: formData.studentId,
      nickname: formData.nickname,
      password: formData.password
    })

    if (res.data && res.data.code === 200) {
      showSuccessToast('注册成功！快去登录吧')
      // 注册成功后，延迟一小会儿跳转回登录页，让提示飞一会儿
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    }
  } catch (error) {
    console.error('注册失败:', error)
    showFailToast(error.response?.data?.error || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}
.logo-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 30px;
}
.app-title {
  margin-top: 16px;
  color: #323233;
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 2px;
}
.register-form {
  margin-top: 10px;
}
</style>