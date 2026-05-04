import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { setupVant } from './plugins/vant'
import axios from 'axios' // 引入 axios

// ================== 新增：Axios 全局拦截器 ==================
// 请求拦截器：在浏览器发出请求之前，自动执行这里的代码
axios.interceptors.request.use(
  config => {
    // 从保险柜拿出门票
    const token = localStorage.getItem('token')
    if (token) {
      // 如果有门票，就把它放进请求头 (Headers) 的 Authorization 字段里
      // 这里的 'Bearer ' 是业界标准的 JWT 前缀，注意后面有个空格！
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)
// ==========================================================

const app = createApp(App)

setupVant(app)
app.use(router)
app.mount('#app')