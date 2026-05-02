<template>
  <div class="publish-page">
    <!-- 顶部导航 -->
    <van-nav-bar title="发布新任务" left-arrow @click-left="onClickLeft" />

    <!-- 阶段一：自然语言输入区 -->
    <div class="input-section">
      <van-cell-group inset>
        <van-field
          v-model="rawContent"
          rows="3"
          autosize
          type="textarea"
          maxlength="100"
          placeholder="一句话描述需求，例如：明天中午求个同学去南区快递点帮拿个大件，打赏5块钱"
          show-word-limit
          :disabled="isParsing"
        />
      </van-cell-group>

      <!-- 智能解析按钮区 -->
      <div class="btn-wrap">
        <van-button 
          v-if="!showForm"
          type="primary" 
          block 
          round 
          :loading="isParsing" 
          loading-text="AI 正在努力解析..."
          @click="handleSmartParse"
        >
          ✨ 智能解析并生成表单
        </van-button>
        <van-button 
          v-else
          type="default" 
          block 
          round 
          icon="replay"
          @click="handleSmartParse"
        >
          重新解析
        </van-button>
      </div>
    </div>

    <!-- 阶段二：结构化表单确认区 (解析成功后展开) -->
    <div v-if="showForm" class="form-section transition-box">
      <h3 class="section-title">请核对任务信息</h3>
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="taskData.time"
            name="time"
            label="期望时间"
            placeholder="请确认时间"
            :rules="[{ required: true, message: '请填写期望时间' }]"
          />
          <van-field
            v-model="taskData.location"
            name="location"
            label="任务地点"
            placeholder="请确认地点"
            :rules="[{ required: true, message: '请填写任务地点' }]"
          />
          <van-field
            v-model="taskData.action"
            name="action"
            label="具体动作"
            placeholder="例如：拿大件快递"
            :rules="[{ required: true, message: '请填写具体动作' }]"
          />
          <van-field
            v-model="taskData.reward"
            type="number"
            name="reward"
            label="报酬金额"
            placeholder="纯数字(元)"
            :rules="[{ required: true, message: '请填写报酬金额' }]"
          />
          <van-field
            v-model="taskData.tags"
            name="tags"
            label="任务标签"
            placeholder="多个标签用逗号隔开"
          />
        </van-cell-group>

        <div class="submit-btn-wrap">
          <van-button round block type="success" native-type="submit" :loading="isSubmitting">
            确认无误并发布
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios' // 已经取消注释啦！

// 路由返回逻辑
const onClickLeft = () => {
  showToast('返回上一页')
}

// 核心状态控制
const rawContent = ref('')
const isParsing = ref(false)
const showForm = ref(false)
const isSubmitting = ref(false)

// 结构化表单数据
const taskData = reactive({
  time: '',
  location: '',
  action: '',
  reward: null,
  tags: ''
})

// 阶段一：真实调用 Spring Boot 后端的 /parse 接口
const handleSmartParse = async () => {
  if (!rawContent.value.trim()) {
    showToast('请先输入您的需求描述');
    return;
  }

  isParsing.value = true;
  showForm.value = false;

  try {
    // 调用真实的后端解析接口
    const res = await axios.post('http://localhost:8080/api/tasks/parse', { 
      text: rawContent.value 
    });
    
    // 获取后端返回的 AI 解析数据
    const parsedData = res.data.ai_parsed_data;

    // 将 AI 提取的数据映射到表单中
    taskData.time = parsedData.time || '';
    taskData.location = parsedData.location || '';
    taskData.action = parsedData.action || '';
    taskData.reward = parsedData.reward || null;
    
    // 后端返回的 tags 是数组 ["跑腿", "急单"]，前端表单需要逗号拼接的字符串 "跑腿,急单"
    taskData.tags = parsedData.tags ? parsedData.tags.join(',') : '';

    showForm.value = true;
    showSuccessToast('解析成功，请核对表单');
  } catch (error) {
    console.error(error);
    showFailToast('AI 开小差了，请手动填写表单');
    showForm.value = true; // 即使失败也让用户手动填
  } finally {
    isParsing.value = false;
  }
}

// 阶段二：真实调用 Spring Boot 后端的 /publish 接口落库
const onSubmit = async (values) => {
  isSubmitting.value = true;
  
  // 组装最终要发送给后端的数据，必须严格匹配 Java 的 TaskPublishRequest DTO
  const finalPayload = {
    publisherId: 1, // 模拟当前登录用户的 ID
    rawContent: rawContent.value,
    aiParsedData: {
      time: values.time,
      location: values.location,
      action: values.action,
      reward: Number(values.reward), // 确保转为数字
      // 前端表单是字符串 "跑腿,急单"，传给后端要劈开成数组 ["跑腿", "急单"]
      tags: values.tags ? values.tags.split(',').map(t => t.trim()) : [] 
    }
  }

  try {
    const res = await axios.post('http://localhost:8080/api/tasks/publish', finalPayload);
    if (res.status === 200) {
      showSuccessToast('任务发布成功！');
      // 发布成功后，重置页面状态
      rawContent.value = '';
      showForm.value = false;
      // TODO: 真实业务中可以在这里 router.push('/tasks') 跳转到任务大厅
    }
  } catch (error) {
    console.error(error);
    showFailToast(error.response?.data?.error || '服务器异常，发布失败');
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.publish-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.input-section {
  padding-top: 16px;
}

.btn-wrap {
  margin: 16px;
}

.form-section {
  margin-top: 24px;
}

.section-title {
  margin: 0 16px 12px;
  color: #323233;
  font-size: 14px;
  font-weight: normal;
}

.submit-btn-wrap {
  margin: 24px 16px;
}

/* 简单的过渡动画效果 */
.transition-box {
  animation: slideDown 0.4s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>