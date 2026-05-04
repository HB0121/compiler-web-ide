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

export default router