<template>
  <div class="hall-container">
    <van-nav-bar title="校园帮办大厅" fixed placeholder />

    <!-- 任务列表渲染区 -->
    <div class="task-list">
      <!-- 空状态提示 -->
      <van-empty v-if="!loading && taskList.length === 0" description="暂无任务，快去发布吧！" />

      <!-- 加载动画 -->
      <van-loading v-if="loading" size="24px" vertical>加载中...</van-loading>

      <!-- 任务卡片列表 -->
      <div class="task-card" v-for="task in taskList" :key="task.taskId">
        
        <!-- 卡片头部：任务动作与金额 -->
        <div class="card-header">
          <span class="action-title">{{ task.aiParsedData?.action || '互助任务' }}</span>
          <span class="reward-price">
            <span class="currency">￥</span>{{ task.rewardAmount || 0 }}
          </span>
        </div>

        <!-- 卡片中部：原始需求与具体信息 -->
        <div class="card-body">
          <div class="raw-content">"{{ task.rawContent }}"</div>
          <div class="meta-info">
            <div class="info-item">
              <van-icon name="location-o" />
              <span>{{ task.aiParsedData?.location || '地点未指定' }}</span>
            </div>
            <div class="info-item">
              <van-icon name="clock-o" />
              <span>{{ task.aiParsedData?.time || '时间未指定' }}</span>
            </div>
          </div>
        </div>

        <!-- 卡片底部：AI 生成的标签与接单按钮 -->
        <div class="card-footer">
          <div class="tags-wrap">
            <van-tag 
              v-for="(tag, index) in task.aiParsedData?.tags" 
              :key="index" 
              plain 
              type="primary" 
              color="#1989fa"
              class="custom-tag"
            >
              {{ tag }}
            </van-tag>
          </div>
          <van-button size="small" type="primary" round class="grab-btn" @click="handleGrab(task.taskId)">
            抢单
          </van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// 【修复点 1】：必须引入这三个方法，否则调用时会报错阻塞运行
import { showToast, showSuccessToast, showFailToast } from 'vant' 
import axios from 'axios'

const taskList = ref([])
const loading = ref(true)

// 发起请求，获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:8080/api/tasks/list')
    if (res.data && res.data.code === 200) {
      taskList.value = res.data.data
    } else {
      showToast(res.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取任务大厅报错:', error)
    showToast('网络请求异常，请稍后再试')
  } finally {
    loading.value = false
  }
}

// 页面加载完成后自动获取数据
onMounted(() => {
  fetchTasks()
})

// 真实的抢单功能接入 (使用乐观更新)
const handleGrab = async (taskId) => {
  try {
    // 调用我们刚写好的后端抢单接口
    const res = await axios.post(`http://localhost:8080/api/tasks/grab/${taskId}`)
    
    if (res.status === 200) {
      // 提示成功
      showSuccessToast('抢单成功！')
      
      // 【修复点 2：乐观更新核心逻辑】
      // 不去调用 fetchTasks() 重新请求后端了。
      // 直接在现有的 taskList 里，把刚才被抢单的那个 task 过滤掉。
      // Vue 的响应式系统发现数组变了，会瞬间让对应的卡片从页面上消失。
      taskList.value = taskList.value.filter(task => task.taskId !== taskId)
    }
  } catch (error) {
    console.error('抢单报错:', error)
    const errorMsg = error.response?.data?.error || '手慢了，抢单失败'
    showFailToast(errorMsg)
  }
}
</script>

<style scoped>
.hall-container {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: 20px;
}

.task-list {
  padding: 12px;
}

.task-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.action-title {
  font-size: 16px;
  font-weight: bold;
  color: #323233;
}

.reward-price {
  font-size: 18px;
  font-weight: bold;
  color: #ee0a24;
}

.currency {
  font-size: 14px;
}

.card-body {
  margin-bottom: 12px;
}

.raw-content {
  font-size: 14px;
  color: #666;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 8px;
  line-height: 1.5;
  word-break: break-all;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #969799;
  font-size: 13px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #ebedf0;
  padding-top: 12px;
}

.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.custom-tag {
  border-radius: 4px;
}

.grab-btn {
  padding: 0 20px;
  background: linear-gradient(to right, #ff6034, #ee0a24);
  border: none;
}
</style>