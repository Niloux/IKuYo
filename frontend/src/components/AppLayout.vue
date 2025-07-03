<template>
  <div
    class="app-layout"
    :style="{ '--header-height': headerHeight + 'px', '--footer-height': footerHeight + 'px' }"
  >
    <!-- 应用头部 -->
    <AppHeader />

    <!-- 主要内容区域 -->
    <main class="main-content">
      <div class="content-container">
        <slot />
      </div>
    </main>

    <!-- 页脚（可选） -->
    <footer class="app-footer">
      <div class="footer-container">
        <p class="footer-text">
          © {{ currentYear }} IKuYo - 追番助手 | 让追番更简单
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import AppHeader from './AppHeader.vue'
import { ref, onMounted, computed } from 'vue'

const headerHeight = ref(0)
const footerHeight = ref(0)
const currentYear = computed(() => new Date().getFullYear())

onMounted(() => {
  // 获取AppHeader的实际高度
  const headerElement = document.querySelector('.app-header')
  if (headerElement) {
    headerHeight.value = headerElement.clientHeight
  }

  // 获取app-footer的实际高度
  const footerElement = document.querySelector('.app-footer')
  if (footerElement) {
    footerHeight.value = footerElement.clientHeight
  }
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.main-content {
  flex: 1;
  width: 100%;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: calc(100vh - var(--header-height, 70px) - var(--footer-height, 70px));
}

.app-footer {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin-top: auto;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
  text-align: center;
}

.footer-text {
  color: #64748b;
  font-size: 0.875rem;
  margin: 0;
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-container {
    padding: 1.5rem 1rem;
    min-height: calc(100vh - var(--header-height, 65px) - var(--footer-height, 60px));
  }

  .footer-container {
    padding: 1rem;
  }

  .footer-text {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .content-container {
    padding: 1rem 0.75rem;
  }
}
</style>
