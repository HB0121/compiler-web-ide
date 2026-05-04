<template>
  <div class="mine-container">
    <!-- 顶部导航 -->
    <van-nav-bar title="个人中心" fixed placeholder />

    <!-- 用户信息卡片 -->
    <div class="user-profile">
      <div class="avatar-wrap">
        <!-- Vant 的默认头像图标 -->
        <van-icon name="user-circle-o" size="64" color="#ebedf0" />
      </div>
      <div class="user-info">
        <div class="username">同学_89757</div>
        <div class="student-id">学号认证：已认证</div>
      </div>
    </div>

    <!-- 数据统计区域 -->
    <van-grid :column-num="3" class="stats-grid">
      <van-grid-item text="发出的任务">
        <template #icon><span class="stats-num">12</span></template>
      </van-grid-item>
      <van-grid-item text="接取的任务">
        <template #icon><span class="stats-num">5</span></template>
      </van-grid-item>
      <van-grid-item text="累计收益">
        <template #icon><span class="stats-num price">￥68</span></template>
      </van-grid-item>
    </van-grid>

    <!-- 功能列表 -->
    <van-cell-group inset class="action-list">
      <van-cell title="我发布的" icon="orders-o" is-link to="/my-tasks?type=published" />
      <van-cell title="我接单的" icon="flag-o" is-link to="/my-tasks?type=grabbed" />
      <van-cell title="钱包余额" icon="balance-o" is-link value="￥68.00" />
    </van-cell-group>

    <van-cell-group inset class="action-list">
      <van-cell title="联系客服" icon="service-o" is-link />
      <van-cell title="设置" icon="setting-o" is-link />
    </van-cell-group>
  </div>
</template>

<script setup>
// 目前主要是静态展示，后续可以接入后端的个人信息查询接口
</script>

<style scoped>
.mine-container {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.user-profile {
  display: flex;
  align-items: center;
  padding: 24px 20px;
  background: linear-gradient(to right, #1989fa, #5fb8fb); /* 漂亮的渐变蓝背景 */
  color: white;
}

.avatar-wrap {
  margin-right: 16px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 4px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.username {
  font-size: 20px;
  font-weight: bold;
}

.student-id {
  font-size: 13px;
  opacity: 0.8;
}

.stats-grid {
  margin-bottom: 12px;
}

.stats-num {
  font-size: 20px;
  font-weight: bold;
  color: #323233;
}

.price {
  color: #ee0a24;
}

.action-list {
  margin-bottom: 12px;
}
</style>