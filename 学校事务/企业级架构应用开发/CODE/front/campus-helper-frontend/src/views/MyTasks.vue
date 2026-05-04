<template>
  <div class="my-tasks-container">
    <!-- 顶部导航 -->
    <van-nav-bar 
      title="我的任务" 
      left-arrow 
      @click-left="$router.back()" 
      fixed 
      placeholder 
    />

    <!-- 双标签页切换 -->
    <van-tabs v-model:active="activeTab" @change="onTabChange" color="#1989fa" sticky offset-top="46">
      
      <!-- ================= 标签1：我发布的 ================= -->
      <van-tab title="我发布的" name="published">
        <div class="task-list">
          <!-- 骨架屏或空状态 -->
          <van-empty v-if="publishedList.length === 0 && !loading" description="暂无发布的任务" />
          
          <!-- 任务卡片 -->
          <div v-for="task in publishedList" :key="task.taskId" class="task-card">
            <div class="card-header">
              <span class="task-id">订单号: {{ task.taskId }}</span>
              <span :class="['task-status', 'status-' + task.status]">{{ formatStatus(task.status) }}</span>
            </div>
            <div class="card-body">
              <div class="task-content">{{ task.rawContent }}</div>
              <div class="task-reward">赏金: <span class="price">￥{{ task.rewardAmount }}</span></div>
            </div>
            
            <!-- 仅当状态为 "1" (进行中) 时，才显示确认完成按钮 -->
            <div class="card-footer" v-if="task.status === '1'">
              <van-button size="small" type="success" plain round @click="openReviewDialog(task.taskId)">
                确认完成
              </van-button>
            </div>
          </div>
        </div>
      </van-tab>

      <!-- ================= 标签2：我接单的 ================= -->
      <van-tab title="我接单的" name="grabbed">
        <div class="task-list">
          <van-empty v-if="grabbedList.length === 0 && !loading" description="暂无接到的任务" />
          
          <div v-for="task in grabbedList" :key="task.taskId" class="task-card">
            <div class="card-header">
              <span class="task-id">订单号: {{ task.taskId }}</span>
              <span :class="['task-status', 'status-' + task.status]">{{ formatStatus(task.status) }}</span>
            </div>
            <div class="card-body">
              <div class="task-content">{{ task.rawContent }}</div>
              <div class="task-reward">赏金: <span class="price">￥{{ task.rewardAmount }}</span></div>
            </div>
            <div class="card-footer" v-if="task.status === '0'">
              <span class="wait-text">等待发布者确认...</span>
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- ================= 核心业务：评价与结算弹窗 ================= -->
    <van-dialog 
      v-model:show="showReviewDialog" 
      title="评价本次服务" 
      show-cancel-button 
      @confirm="submitReview"
    >
      <div style="padding: 20px; text-align: center;">
        <div style="margin-bottom: 10px; color: #666; font-size: 14px;">给帮忙的同学打个分吧</div>
        <van-rate v-model="reviewForm.rating" :size="30" color="#ffd21e" void-icon="star" void-color="#eee" />
      </div>
      <van-field
        v-model="reviewForm.comment"
        rows="2"
        autosize
        type="textarea"
        maxlength="50"
        placeholder="写点什么评价一下对方吧... (选填)"
        show-word-limit
      />
    </van-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios'

const route = useRoute()
const activeTab = ref('published')
const loading = ref(false)

const publishedList = ref([])
const grabbedList = ref([])

// 弹窗相关响应式变量
const showReviewDialog = ref(false)
const currentProcessingTaskId = ref(null)
const reviewForm = ref({
  rating: 5,
  comment: ''
})

// === 生命周期：页面加载时初始化 ===
onMounted(() => {
  // 从个人中心点进来时，根据 url 参数自动跳到对应的 Tab
  if (route.query.type) {
    activeTab.value = route.query.type
  }
  fetchData()
})

// === 核心方法：拉取数据 ===
const fetchData = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'published') {
      const res = await axios.get('http://localhost:8080/api/tasks/my-published')
      if (res.data.code === 200) {
        publishedList.value = res.data.data
      }
    } else {
      const res = await axios.get('http://localhost:8080/api/tasks/my-grabbed')
      if (res.data.code === 200) {
        grabbedList.value = res.data.data
      }
    }
  } catch (error) {
    console.error('获取列表失败:', error)
    showToast('获取列表数据失败')
  } finally {
    loading.value = false
  }
}

// 切换 Tab 时重新拉取数据
const onTabChange = () => {
  fetchData()
}

// === 状态字典翻译 ===
const formatStatus = (status) => {
  const map = {
    '0': '待接单',
    '1': '进行中',
    '2': '已完成',
    '3': '已取消'
  }
  return map[status] || '未知状态'
}

// === 弹窗操作 ===
const openReviewDialog = (taskId) => {
  currentProcessingTaskId.value = taskId
  // 每次打开弹窗前，重置表单为默认 5 星好评
  reviewForm.value = { rating: 5, comment: '' } 
  showReviewDialog.value = true
}

// === 提交评价与结算 ===
const submitReview = async () => {
  const taskId = currentProcessingTaskId.value
  try {
    // 呼叫后端的完成接口，带上评分和评价内容
    const res = await axios.post(`http://localhost:8080/api/tasks/complete/${taskId}`, {
      rating: reviewForm.value.rating,
      comment: reviewForm.value.comment || '默认好评！'
    })
    
    if (res.data && res.data.code === 200) {
      showSuccessToast('结算与评价成功！')
      
      // 乐观更新：在前端直接把这个任务的状态改成 "2" (已完成)
      const task = publishedList.value.find(t => t.taskId === taskId)
      if (task) {
        task.status = '2'
      }
    }
  } catch (error) {
    console.error('确认完成报错:', error)
    showFailToast(error.response?.data?.error || '操作失败')
  }
}
</script>

<style scoped>
.my-tasks-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}
.task-list {
  padding: 12px;
  padding-bottom: 60px; /* 留出底部空间 */
}
.task-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
  margin-bottom: 10px;
}
.task-id {
  font-size: 13px;
  color: #999;
}
.task-status {
  font-size: 13px;
  font-weight: bold;
}
/* 状态颜色动态变化 */
.status-0 { color: #ff976a; } /* 待接单：橙色 */
.status-1 { color: #1989fa; } /* 进行中：蓝色 */
.status-2 { color: #07c160; } /* 已完成：绿色 */

.card-body {
  margin-bottom: 12px;
}
.task-content {
  font-size: 15px;
  color: #323233;
  line-height: 1.5;
  margin-bottom: 8px;
  font-weight: 500;
}
.task-reward {
  font-size: 13px;
  color: #666;
}
.price {
  color: #ee0a24;
  font-weight: bold;
  font-size: 16px;
}
.card-footer {
  display: flex;
  justify-content: flex-end;
  border-top: 1px dashed #f0f0f0;
  padding-top: 10px;
}
.wait-text {
  font-size: 12px;
  color: #999;
}
</style>