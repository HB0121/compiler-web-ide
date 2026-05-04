import { createRouter, createWebHistory } from 'vue-router'

import PublishPage from '../views/PublishPage.vue'
import TaskHall from '../views/TaskHall.vue'
import Mine from '../views/Mine.vue'
import MyTasks from '../views/MyTasks.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

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
    path: '/register',
    name: 'Register',
    component: Register
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
  const token = localStorage.getItem('token')
  
  // 核心逻辑：如果他去的既不是登录页，也不是注册页，而且又没带门票，就踢回登录页
  if (to.path !== '/login' && to.path !== '/register' && !token) {
    next('/login')
  } else {
    // 其他所有情况（有门票，或者是去登录/注册页）全部放行
    next()
  }
})

export default router