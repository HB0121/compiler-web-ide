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
          
          <!-- ================= 新增：任务附图上传 ================= -->
          <van-field name="uploader" label="添加附图">
            <template #input>
              <van-uploader 
                v-model="fileList" 
                :max-count="1" 
                :after-read="afterRead"
                upload-text="上传截图"
              />
            </template>
          </van-field>
          <!-- ====================================================== -->
          
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
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import axios from 'axios'

const router = useRouter()

// 路由返回逻辑
const onClickLeft = () => {
  router.back()
}

// 核心状态控制
const rawContent = ref('')
const isParsing = ref(false)
const showForm = ref(false)
const isSubmitting = ref(false)

// ======== 新增：图片上传相关变量 ========
const fileList = ref([])
const uploadedImageUrl = ref('')

// 结构化表单数据
const taskData = reactive({
  time: '',
  location: '',
  action: '',
  reward: null,
  tags: ''
})

// 获取 Token 的通用方法
const getTokenHeaders = () => {
  return {
    Authorization: `Bearer ${localStorage.getItem('token')}`
  }
}

// ================= 新增：处理图片上传逻辑 =================
const afterRead = async (file) => {
  file.status = 'uploading'
  file.message = '上传中...'

  // 构建 FormData
  const formData = new FormData()
  formData.append('file', file.file)

  try {
    const res = await axios.post('http://localhost:8080/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...getTokenHeaders() // 带上 JWT 门票
      }
    })

    if (res.data.code === 200) {
      file.status = 'done'
      uploadedImageUrl.value = res.data.data.url // 保存后端返回的真实图片地址
    } else {
      throw new Error('上传失败')
    }
  } catch (error) {
    file.status = 'failed'
    file.message = '上传出错'
    console.error('上传异常', error)
  }
}
// ==========================================================

// 阶段一：真实调用 Spring Boot 后端的 /parse 接口
const handleSmartParse = async () => {
  if (!rawContent.value.trim()) {
    showToast('请先输入您的需求描述')
    return
  }

  isParsing.value = true
  showForm.value = false

  try {
    // 增加 headers 携带 token，防止被安检门拦住
    const res = await axios.post('http://localhost:8080/api/tasks/parse', 
      { text: rawContent.value },
      { headers: getTokenHeaders() }
    )
    
    const parsedData = res.data.ai_parsed_data

    taskData.time = parsedData.time || ''
    taskData.location = parsedData.location || ''
    taskData.action = parsedData.action || ''
    taskData.reward = parsedData.reward || null
    taskData.tags = parsedData.tags ? parsedData.tags.join(',') : ''

    showForm.value = true
    showSuccessToast('解析成功，请核对表单')
  } catch (error) {
    console.error(error)
    showFailToast('AI 开小差了，请手动填写表单')
    showForm.value = true
  } finally {
    isParsing.value = false
  }
}

// 阶段二：真实调用 Spring Boot 后端的 /publish 接口落库
const onSubmit = async (values) => {
  isSubmitting.value = true
  
  // 组装最终要发送给后端的数据
  const finalPayload = {
    // publisherId 已经删掉，后端直接从 token 里解析
    rawContent: rawContent.value,
    imageUrl: uploadedImageUrl.value, // 新增：把上传成功拿到的图片URL塞进去
    aiParsedData: {
      time: values.time,
      location: values.location,
      action: values.action,
      reward: Number(values.reward),
      tags: values.tags ? values.tags.split(',').map(t => t.trim()) : [] 
    }
  }

  try {
    const res = await axios.post('http://localhost:8080/api/tasks/publish', finalPayload, {
      headers: getTokenHeaders() // 带上门票
    })
    
    if (res.status === 200) {
      showSuccessToast('任务发布成功！')
      
      // 重置状态
      rawContent.value = ''
      fileList.value = []
      uploadedImageUrl.value = ''
      showForm.value = false
      
      // 成功后自动跳回大厅
      setTimeout(() => {
        router.push('/hall')
      }, 1000)
    }
  } catch (error) {
    console.error(error)
    showFailToast(error.response?.data?.error || '服务器异常，发布失败')
  } finally {
    isSubmitting.value = false
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