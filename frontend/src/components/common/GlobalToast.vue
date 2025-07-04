<!--
  GlobalToast.vue
  全局消息提示组件：用于显示全局Toast消息，通常由feedbackStore.showToast推送
  只需在主布局(AppLayout.vue)中挂载一次，全局可用
-->
<template>
  <transition-group name="toast-fade" tag="div" class="global-toast-container">
    <div v-for="toast in toasts" :key="toast.id" :class="['global-toast', toast.type]">
      {{ toast.message }}
    </div>
  </transition-group>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFeedbackStore } from '../../stores/feedbackStore';

const feedbackStore = useFeedbackStore();
const toasts = computed(() => feedbackStore.toasts);
</script>

<style scoped>
.global-toast-container {
  position: fixed;
  top: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.global-toast {
  min-width: 180px;
  max-width: 320px;
  background: #fff;
  color: #333;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  padding: 12px 20px;
  font-size: 15px;
  opacity: 0.95;
  transition: background 0.2s;
}
.global-toast.success { background: #e6ffed; color: #2ecc40; }
.global-toast.error { background: #ffeaea; color: #e74c3c; }
.global-toast.info { background: #eaf6ff; color: #3498db; }
.toast-fade-enter-active, .toast-fade-leave-active {
  transition: all 0.3s;
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
