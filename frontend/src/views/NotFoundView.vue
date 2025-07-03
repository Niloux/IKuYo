<template>
  <div class="not-found-container">
    <h1 class="not-found-title">404</h1>
    <p class="not-found-message">抱歉，您访问的页面不存在。</p>
    <router-link to="/" class="home-link">返回首页</router-link>
  </div>
</template>

<script setup lang="ts">
// 这是一个简单的静态页面，无需复杂逻辑
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 70vh; /* 确保在页面中央 */
  text-align: center;
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  margin: 3rem auto;
}

.not-found-title {
  font-size: 6rem;
  font-weight: bold;
  color: #e74c3c;
  margin-bottom: 1rem;
}

.not-found-message {
  font-size: 1.5rem;
  color: #34495e;
  margin-bottom: 2rem;
}

.home-link {
  display: inline-block;
  padding: 0.8rem 1.5rem;
  background-color: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  transition: background-color 0.3s ease;
}

.home-link:hover {
  background-color: #2980b9;
}
</style>
