import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { setupVant } from './plugins/vant' // 抽离的配置

const app = createApp(App)

// 1. 注册 Vant UI
setupVant(app)

// 2. 注册路由
app.use(router)

// 3. 挂载应用
app.mount('#app')