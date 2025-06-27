<template>
  <transition name="scroll-to-top" appear>
    <button 
      v-show="isVisible"
      class="scroll-to-top-btn"
      :class="{ 'scrolling': isScrolling }"
      @click="scrollToTop"
      :aria-label="'返回顶部'"
      :disabled="isScrolling"
    >
      <svg 
        class="arrow-icon" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2"
      >
        <path d="m18 15-6-6-6 6"/>
      </svg>
    </button>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { smoothScrollToTop } from '../utils/scrollUtils'

// 按钮显示状态
const isVisible = ref(false)
// 滚动中状态
const isScrolling = ref(false)

// 滚动阈值
const SCROLL_THRESHOLD = 400

// 滚动事件处理函数
const handleScroll = () => {
  isVisible.value = window.scrollY > SCROLL_THRESHOLD
}

// 点击滚动到顶部
const scrollToTop = () => {
  if (isScrolling.value) return // 防止重复点击
  
  isScrolling.value = true
  smoothScrollToTop()
  
  // 滚动完成后重置状态
  setTimeout(() => {
    isScrolling.value = false
  }, 1000) // 假设滚动动画持续1秒
}

// 组件挂载时添加滚动监听
onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  // 初始检查滚动位置
  handleScroll()
})

// 组件卸载时移除滚动监听
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.scroll-to-top-btn {
  position: fixed;
  top: 110px;
  right: 60px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  outline: none;
  cursor: pointer;
  box-shadow: 
    0 8px 32px rgba(16, 185, 129, 0.3),
    0 2px 8px rgba(16, 185, 129, 0.2);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(20px) saturate(180%);
  z-index: 999;
}

.scroll-to-top-btn::before {
  content: '';
  position: absolute;
  top: 1px;
  left: 1px;
  right: 1px;
  bottom: 1px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.05) 50%,
    rgba(0, 0, 0, 0.05) 100%);
  pointer-events: none;
}

.scroll-to-top-btn:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 
    0 12px 48px rgba(16, 185, 129, 0.4),
    0 4px 16px rgba(16, 185, 129, 0.3);
}

.scroll-to-top-btn:active {
  transform: translateY(-2px) scale(1.02);
}

.scroll-to-top-btn.scrolling {
  animation: scrollingPulse 1s ease-in-out;
  pointer-events: none;
}

@keyframes scrollingPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(0.95);
    opacity: 0.8;
  }
}

.arrow-icon {
  width: 24px;
  height: 24px;
  color: white;
  stroke-width: 2.5;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* 淡入淡出过渡动画 */
.scroll-to-top-enter-active,
.scroll-to-top-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.scroll-to-top-enter-from,
.scroll-to-top-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .scroll-to-top-btn {
    top: 100px;
    right: 30px;
    width: 44px;
    height: 44px;
  }
  
  .arrow-icon {
    width: 20px;
    height: 20px;
  }
}

@media (max-width: 480px) {
  .scroll-to-top-btn {
    top: 95px;
    width: 40px;
    height: 40px;
  }
  
  .arrow-icon {
    width: 18px;
    height: 18px;
  }
}
</style> 