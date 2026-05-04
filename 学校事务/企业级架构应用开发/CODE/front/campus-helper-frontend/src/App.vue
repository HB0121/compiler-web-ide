<template>
  <div class="app-wrapper">
    <!-- 路由视图（画框）：这里会根据网址动态显示 TaskHall 或 PublishPage -->
    <router-view class="main-content" />

    
    <van-tabbar v-show="$route.path !== '/login'" route placeholder active-color="#ee0a24" inactive-color="#000">
      <van-tabbar-item replace to="/hall" icon="home-o">大厅</van-tabbar-item>
      <van-tabbar-item replace to="/publish" icon="plus">发单</van-tabbar-item>
      <van-tabbar-item replace to="/mine" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<style>
/* 全局样式重置 */
html, body {
  margin: 0;
  padding: 0;
  background-color: #f7f8fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
}

.app-wrapper {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 让主体内容区域可以滚动，底部留出 tabbar 的高度 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 50px; /* 防止内容被底部导航栏挡住 */
}
</style>