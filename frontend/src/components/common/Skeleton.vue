<template>
  <!--
    Skeleton骨架屏通用组件
    Props:
      - loading: 是否处于加载中（推荐，支持延迟展示）
      - delay: 延迟展示骨架屏的毫秒数，默认150ms
      - type: 骨架屏类型（card | list | image | custom），决定结构
      - rows: list/custom类型下骨架行数
      - customClass: 额外自定义样式类
    用法示例：
      <Skeleton :loading="loading" type="card" />
      <Skeleton :loading="loading" type="list" :rows="6" :delay="200" />
      <Skeleton type="card" /> <!-- 兼容老用法，无loading时直接渲染骨架屏 -->
  <div v-if="shouldShowSkeleton" :class="['skeleton', type, customClass]">
    <template v-if="type === 'card'">
      <div class="skeleton-card-image" />
      <div class="skeleton-card-content">
        <div class="skeleton-line skeleton-title" />
        <div class="skeleton-line skeleton-subtitle" />
        <div class="skeleton-line skeleton-meta" />
      </div>
    </template>
    <template v-else-if="type === 'list'">
      <div v-for="n in rows" :key="n" class="skeleton-line skeleton-list-item" />
    </template>
    <template v-else-if="type === 'image'">
      <div class="skeleton-image" />
    </template>
    <template v-else>
      <div v-for="n in rows" :key="n" class="skeleton-line" />
    </template>
  </div>
</template>

<script setup lang="ts">
// Skeleton骨架屏通用组件，支持延迟展示
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: undefined, // 兼容老用法
  },
  delay: {
    type: Number,
    default: 150,
  },
  type: {
    type: String,
    default: 'card', // card | list | image | custom
  },
  rows: {
    type: Number,
    default: 3,
  },
  customClass: {
    type: String,
    default: '',
  },
})

const shouldShowSkeleton = ref(props.loading === undefined ? true : false)
let timer: number | null = null

watch(
  () => props.loading,
  (newVal) => {
    if (newVal === undefined) {
      shouldShowSkeleton.value = true // 兼容老用法
      return
    }
    if (newVal) {
      // loading为true，延迟delay毫秒后显示骨架屏
      timer && clearTimeout(timer)
      timer = window.setTimeout(() => {
        shouldShowSkeleton.value = true
      }, props.delay)
    } else {
      // loading为false，立即隐藏骨架屏
      timer && clearTimeout(timer)
      shouldShowSkeleton.value = false
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  timer && clearTimeout(timer)
})
</script>

<style scoped>
.skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}
.skeleton.card {
  width: 100%;
  max-width: 240px;
  border-radius: 8px;
  background: #f8f9fa;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
  padding: 0;
}
.skeleton-card-image {
  width: 100%;
  aspect-ratio: 3/4;
  background: #e0e0e0;
  animation: skeleton-loading 1.2s infinite linear;
}
.skeleton-card-content {
  padding: 0.75rem 1rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.skeleton-line {
  height: 16px;
  background: #e0e0e0;
  border-radius: 4px;
  animation: skeleton-loading 1.2s infinite linear;
}
.skeleton-title {
  width: 70%;
  height: 20px;
}
.skeleton-subtitle {
  width: 50%;
  height: 16px;
}
.skeleton-meta {
  width: 40%;
  height: 14px;
}
.skeleton-list-item {
  width: 100%;
  height: 18px;
  margin-bottom: 0.5rem;
}
.skeleton.image .skeleton-image {
  width: 100%;
  aspect-ratio: 16/9;
  background: #e0e0e0;
  animation: skeleton-loading 1.2s infinite linear;
  border-radius: 8px;
}
@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
