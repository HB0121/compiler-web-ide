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
// import axios from 'axios' // 实际接入后端时取消注释

// 路由返回逻辑模拟
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

// 模拟调用 Spring Boot 后端大模型接口
const handleSmartParse = async () => {
  if (!rawContent.value.trim()) {
    showToast('请先输入您的需求描述');
    return;
  }

  isParsing.value = true;
  showForm.value = false;

  // 模拟网络延迟和 AI 模型处理时间 (1.5秒)
  setTimeout(() => {
    try {
      // 在真实开发中，这里是： const res = await axios.post('/api/tasks/parse', { text: rawContent.value })
      // 下面是模拟后端的伪返回数据，基于简单的正则做个假交互演示
      const mockParsedResult = {
        time: rawContent.value.includes('明天') ? '明天' : '尽快',
        location: rawContent.value.includes('南区') ? '南区快递点' : '校内',
        action: rawContent.value.includes('拿') ? '拿快递' : '其他互助',
        reward: rawContent.value.match(/\d+/) ? rawContent.value.match(/\d+/)[0] : 0,
        tags: '跑腿,帮办'
      }

      // 将解析结果映射到表单
      taskData.time = mockParsedResult.time;
      taskData.location = mockParsedResult.location;
      taskData.action = mockParsedResult.action;
      taskData.reward = mockParsedResult.reward;
      taskData.tags = mockParsedResult.tags;

      showForm.value = true;
      showSuccessToast('解析成功，请核对表单');
    } catch (error) {
      showFailToast('解析异常，请手动填写');
      showForm.value = true; // 即使失败也让用户填
    } finally {
      isParsing.value = false;
    }
  }, 1500)
}

// 模拟提交至后端落库
const onSubmit = (values) => {
  isSubmitting.value = true;
  
  // 组装最终要发送给后端的数据 (包含了原始文本和AI解析后的JSON化数据)
  const finalPayload = {
    raw_content: rawContent.value,
    ai_parsed_data: values
  }

  console.log('提交的数据：', finalPayload);

  setTimeout(() => {
    isSubmitting.value = false;
    showSuccessToast('任务发布成功！');
    // 真实业务中，发布成功后通常通过 router.push('/hall') 跳转回大厅
  }, 1000)
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