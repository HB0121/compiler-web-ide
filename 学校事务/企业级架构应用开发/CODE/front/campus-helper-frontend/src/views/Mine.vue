<template>
  <div class="mine-container">
    <van-nav-bar title="个人中心" fixed placeholder />

    <!-- 头部用户信息 -->
    <div class="user-header">
      <van-image
        round
        width="80px"
        height="80px"
        src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
      />
      <div class="user-info">
        <!-- 动态显示当前登录的用户名 -->
        <div class="user-name">{{ currentUsername || '未登录' }}</div>
        <div class="user-id">ID: {{ currentUserId || '--' }}</div>
      </div>
    </div>

    <!-- 功能列表 -->
    <van-cell-group inset class="action-list">
      <van-cell title="我发布的" icon="orders-o" is-link to="/my-tasks?type=published" />
      <van-cell title="我接单的" icon="flag-o" is-link to="/my-tasks?type=grabbed" />
      <van-cell title="钱包余额" icon="balance-o" is-link value="￥68.00" />
    </van-cell-group>

    <!-- 退出登录按钮 -->
    <div class="logout-wrap">
      <van-button type="danger" block round @click="handleLogout">退出登录</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()

// 响应式变量，用来存从本地拿出来的用户信息
const currentUsername = ref('')
const currentUserId = ref('')

// 页面加载时，去保险柜里拿名字和ID
onMounted(() => {
  currentUsername.value = localStorage.getItem('username')
  currentUserId.value = localStorage.getItem('userId')
})

// 退出登录逻辑
const handleLogout = () => {
  // 1. 清空保险柜里的门票和用户信息
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('userId')
  
  // 2. 提示并跳转回登录页
  showToast('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.mine-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}
.user-header {
  display: flex;
  align-items: center;
  padding: 30px 20px;
  background: linear-gradient(to right, #1989fa, #5cadff);
  color: white;
}
.user-info {
  margin-left: 20px;
}
.user-name {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}
.user-id {
  font-size: 14px;
  opacity: 0.8;
}
.action-list {
  margin-top: 20px;
}
.logout-wrap {
  margin: 40px 16px 20px;
}
</style>