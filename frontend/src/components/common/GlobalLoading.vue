<template>
  <transition name="fade">
    <div v-if="visible" class="global-loading-overlay">
      <div class="spinner"></div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFeedbackStore } from '@/stores/feedbackStore';

const feedbackStore = useFeedbackStore();
const visible = computed(() => feedbackStore.loading);
</script>

<style scoped>
.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255,255,255,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.spinner {
  width: 48px;
  height: 48px;
  border: 6px solid #eee;
  border-top: 6px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
