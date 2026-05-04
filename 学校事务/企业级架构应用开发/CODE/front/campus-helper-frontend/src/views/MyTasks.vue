<template>
  <div class="my-tasks-container">
    <!-- 顶部导航 -->
    <van-nav-bar title="订单管理" left-arrow @click-left="$router.back()" fixed placeholder />

    <!-- 标签页切换 -->
    <van-tabs v-model:active="activeTab" @change="handleTabChange" sticky offset-top="46">
      
      <!-- ================== 我发布的 ================== -->
      <van-tab title="我发布的" name="published">
        <div class="list-wrap">
          <van-loading v-if="loading" vertical>加载中...</van-loading>
          <van-empty v-else-if="publishedList.length === 0" description="您还没有发布过任务" />
          
          <!-- 发布的任务卡片 -->
          <div class="task-card" v-for="task in publishedList" :key="task.taskId">
            <div class="card-header">
              <span class="action-title">{{ task.aiParsedData?.action || '互助任务' }}</span>
              <!-- 动态状态标签：支持 0(待接单), 1(进行中), 2(已完成) -->
              <van-tag :type="task.status === '0' ? 'primary' : (task.status === '1' ? 'success' : 'default')">
                {{ task.status === '0' ? '待接单' : (task.status === '1' ? '进行中' : '已完成') }}
              </van-tag>
            </div>
            <div class="card-body">"{{ task.rawContent }}"</div>
            <div class="card-footer">
              <span class="reward-price">赏金: ￥{{ task.rewardAmount || 0 }}</span>
              
              <!-- 操作按钮：进行中显示绿色的确认完成，已完成显示灰色的不可点击状态 -->
              <van-button 
                v-if="task.status === '1'" 
                size="small" 
                type="success" 
                plain 
                round 
                @click="handleComplete(task.taskId)"
              >
                确认完成
              </van-button>
              <van-button 
                v-else-if="task.status === '2'" 
                size="small" 
                type="default" 
                disabled 
                plain 
                round
              >
                已完成
              </van-button>
            </div>
          </div>
        </div>
      </van-tab>

      <!-- ================== 我接单的 ================== -->
      <van-tab title="我接单的" name="grabbed">
        <div class="list-wrap">
          <van-loading v-if="loading" vertical>加载中...</van-loading>
          <van-empty v-else-if="grabbedList.length === 0" description="您还没有接过单哦" />
          
          <!-- 接到的任务卡片 -->
          <div class="task-card" v-for="task in grabbedList" :key="task.taskId">
            <div class="card-header">
              <span class="action-title">{{ task.aiParsedData?.action || '互助任务' }}</span>
              <!-- 如果状态是 2，说明雇主已经确认完成了 -->
              <van-tag :type="task.status === '2' ? 'default' : 'warning'">
                {{ task.status === '2' ? '已完成' : '待送达' }}
              </van-tag>
            </div>
            <div class="card-body">"{{ task.rawContent }}"</div>
            <div class="card-footer">
              <span class="reward-price">预计收益: ￥{{ task.rewardAmount || 0 }}</span>
              <!-- 同样的，如果已完成，底部按钮也置灰 -->
              <van-button 
                v-if="task.status === '1'" 
                size="small" 
                type="primary" 
                plain 
                round
              >
                联系雇主
              </van-button>
              <van-button 
                v-else-if="task.status === '2'" 
                size="small" 
                type="default" 
                disabled 
                plain 
                round
              >
                赏金已入账
              </van-button>
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// 【修复点】：引入全部需要的 Toast 方法
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios'
import { useRoute } from 'vue-router'

const route = useRoute()
// 默认根据路由传过来的参数决定高亮哪个 Tab
const activeTab = ref(route.query.type || 'published') 

const loading = ref(false)
const publishedList = ref([])
const grabbedList = ref([])

// 获取列表数据
const fetchMyTasks = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'published') {
      const res = await axios.get('http://localhost:8080/api/tasks/my-published')
      publishedList.value = res.data.data || []
    } else {
      const res = await axios.get('http://localhost:8080/api/tasks/my-grabbed')
      grabbedList.value = res.data.data || []
    }
  } catch (error) {
    showToast('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 切换 Tab 时重新拉取数据
const handleTabChange = () => {
  fetchMyTasks()
}

// ================== 新增：确认完成逻辑 ==================
const handleComplete = async (taskId) => {
  try {
    // 呼叫后端确认完成接口
    const res = await axios.post(`http://localhost:8080/api/tasks/complete/${taskId}`)
    if (res.status === 200) {
      showSuccessToast('结算成功！')
      
      // 【乐观更新】：直接在前端数组里修改状态，不需要重新请求后端
      const task = publishedList.value.find(t => t.taskId === taskId)
      if (task) {
        task.status = '2' // 改为已完成
      }
    }
  } catch (error) {
    console.error('确认完成报错:', error)
    showFailToast(error.response?.data?.error || '操作失败')
  }
}

onMounted(() => {
  fetchMyTasks()
})
</script>

<style scoped>
.my-tasks-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}
.list-wrap {
  padding: 12px;
}
.task-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: bold;
}
.card-body {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.reward-price {
  color: #ee0a24;
  font-weight: bold;
}
</style>