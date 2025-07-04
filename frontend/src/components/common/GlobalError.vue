<!--
  GlobalError.vue
  全局错误弹窗组件：用于显示全局错误信息，通常由feedbackStore.showError推送
  只需在主布局(AppLayout.vue)中挂载一次，全局可用
-->
<template>
  <transition name="fade">
    <div v-if="visible" class="global-error-overlay">
      <div class="global-error-box scale-in">
        <div class="global-error-title">发生错误</div>
        <div class="global-error-message">{{ errorMessage }}</div>
        <button class="global-error-close" @click="close">关闭</button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFeedbackStore } from '../../stores/feedbackStore';

const feedbackStore = useFeedbackStore();
const visible = computed(() => !!feedbackStore.error);
const errorMessage = computed(() => feedbackStore.error || '');
const close = () => feedbackStore.clearError();
</script>

<style scoped>
.global-error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255,0,0,0.08);
  z-index: 2200;
  display: flex;
  align-items: center;
  justify-content: center;
}
.global-error-box {
  background: #fff;
  border: 1.5px solid #e74c3c;
  border-radius: 8px;
  padding: 32px 40px;
  box-shadow: 0 2px 16px rgba(231,76,60,0.08);
  min-width: 320px;
  max-width: 90vw;
  text-align: center;
}
.global-error-title {
  font-size: 20px;
  color: #e74c3c;
  margin-bottom: 12px;
  font-weight: bold;
}
.global-error-message {
  font-size: 16px;
  color: #333;
  margin-bottom: 24px;
}
.global-error-close {
  background: #e74c3c;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 24px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.global-error-close:hover {
  background: #c0392b;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
