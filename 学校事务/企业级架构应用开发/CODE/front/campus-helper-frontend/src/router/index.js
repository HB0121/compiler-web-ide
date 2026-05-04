import { createRouter, createWebHistory } from 'vue-router'

import PublishPage from '../views/PublishPage.vue'
import TaskHall from '../views/TaskHall.vue'
import Mine from '../views/Mine.vue'
import MyTasks from '../views/MyTasks.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/',
    redirect: '/login' // 默认一打开网址，就跳转到大厅
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/hall',
    name: 'Hall',
    component: TaskHall
  },
  {
    path: '/publish',
    name: 'Publish',
    component: PublishPage
  },
  {
    path: '/mine',
    name: 'Mine',
    component: Mine
  },
  {
    path: '/my-tasks',
    name: 'MyTasks',
    component: MyTasks
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // 1. 去保险柜（localStorage）里看看有没有 token
  const token = localStorage.getItem('token')
  
  // 2. 如果他想去的页面不是登录页，而且他又没有 token，就强制踢回登录页
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    // 3. 其他情况（比如有 token，或者他本来就在登录页），直接放行
    next()
  }
})

export default router