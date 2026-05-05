<template>
  <div class="mine-container">
    <van-nav-bar title="个人中心" fixed placeholder />

    <!-- 顶部个人资料卡片 -->
    <div class="user-profile">
      <van-image
        round
        width="80px"
        height="80px"
        src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
      />
      <div class="user-info">
        <!-- 动态显示后端的昵称和学号 -->
        <h3 class="nickname">{{ userInfo.nickname || '神秘同学' }}</h3>
        <span class="student-id">学号: {{ userInfo.studentId || '未知' }}</span>
      </div>
    </div>

    <!-- 核心业务数据统计区：虚拟钱包与信用分 -->
    <div class="user-stats">
      <div class="stat-item">
        <!-- 动态显示余额，并保留两位小数 -->
        <div class="stat-value balance">￥{{ userInfo.balance ? userInfo.balance.toFixed(2) : '0.00' }}</div>
        <div class="stat-label">钱包余额</div>
      </div>
      <div class="stat-item">
        <!-- 动态显示信用分 -->
        <div class="stat-value credit">{{ userInfo.creditScore || 0 }}</div>
        <div class="stat-label">信用分</div>
      </div>
    </div>

    <!-- 功能列表菜单 -->
    <van-cell-group inset class="menu-group">
      <van-cell title="我发布的任务" icon="send-gift-o" is-link @click="goToMyTasks('published')" />
      <van-cell title="我接到的任务" icon="logistics" is-link @click="goToMyTasks('grabbed')" />
      <van-cell title="修改密码" icon="edit" is-link />
      <van-cell title="关于校园帮办" icon="info-o" is-link />
    </van-cell-group>

    <!-- 退出登录按钮 -->
    <div style="margin: 24px 16px;">
      <van-button round block type="danger" plain @click="handleLogout">
        退出登录
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import axios from 'axios'

const router = useRouter()

// 定义响应式的用户信息，初始给个兜底默认值
const userInfo = ref({
  nickname: '',
  studentId: '',
  balance: 0.00,
  creditScore: 100
})

// === 生命周期：页面加载时拉取后端数据 ===
onMounted(() => {
  fetchUserInfo()
})

// === 核心：呼叫后端的 /info 接口 ===
const fetchUserInfo = async () => {
  try {
    // 加上 token 进行鉴权请求
    const res = await axios.get('http://localhost:8080/api/user/info', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (res.data && res.data.code === 200) {
      // 将后端返回的真实用户数据赋给前端变量
      userInfo.value = res.data.data
    }
  } catch (error) {
    console.error('获取个人信息失败', error)
    showToast('获取用户信息失败，请重新登录')
  }
}

// 跳转到“我的任务”页面，并传参决定激活哪个 Tab
const goToMyTasks = (type) => {
  router.push({
    path: '/my-tasks',
    query: { type: type }
  })
}

// 退出登录逻辑
const handleLogout = () => {
  showConfirmDialog({
    title: '退出登录',
    message: '确定要退出当前账号吗？',
  }).then(() => {
    // 清除本地缓存的门票
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userId')
    
    // 跳回登录页
    router.replace('/login')
  }).catch(() => {
    // 点击取消，什么都不做
  })
}
</script>

<style scoped>
.mine-container {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: 60px;
}

.user-profile {
  background: linear-gradient(135deg, #1989fa, #0570db);
  padding: 40px 20px 30px;
  display: flex;
  align-items: center;
  color: white;
}

.user-info {
  margin-left: 20px;
}

.nickname {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.student-id {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 6px;
  display: inline-block;
}

.user-stats {
  display: flex;
  background: white;
  margin: -16px 16px 16px;
  border-radius: 8px;
  padding: 16px 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  position: relative;
  z-index: 10;
}

.stat-item {
  flex: 1;
  text-align: center;
  border-right: 1px solid #f0f0f0;
}
.stat-item:last-child {
  border-right: none;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 4px;
}

/* 钱包显示红色，信用分显示橙色，更有视觉冲击力 */
.balance { color: #ee0a24; }
.credit { color: #ff976a; }

.stat-label {
  font-size: 13px;
  color: #666;
}

.menu-group {
  margin-top: 20px;
}
</style>