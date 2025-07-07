<!--
  GlobalToast.vue
  全局消息提示组件：用于显示全局Toast消息，通常由feedbackStore.showToast推送
  只需在主布局(AppLayout.vue)中挂载一次，全局可用
-->
<template>
  <transition name="toast-fade">
    <div v-if="toast" :key="toast.id" :class="['global-toast', toast.type]">
      <span class="toast-message">{{ toast.message }}</span>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFeedbackStore } from '../../stores/feedbackStore';

const feedbackStore = useFeedbackStore();
const toast = computed(() => feedbackStore.toast);
</script>

<style scoped>
.global-toast-container {
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.global-toast {
  min-width: 200px;
  max-width: 340px;
  background: #fff;
  color: #333;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  padding: 14px 28px 14px 20px;
  font-size: 15px;
  opacity: 0.97;
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  font-weight: 500;
  letter-spacing: 0.01em;
  box-sizing: border-box;
}
.global-toast.success { background: #e6ffed; color: #2ecc40; }
.global-toast.error { background: #ffeaea; color: #e74c3c; }
.global-toast.info { background: #eaf6ff; color: #3498db; }
.toast-message {
  flex: 1;
  text-align: center;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.01em;
}
.toast-fade-enter-active, .toast-fade-leave-active {
  transition: all 0.3s cubic-bezier(.4,0,.2,1);
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-24px);
}
</style>
