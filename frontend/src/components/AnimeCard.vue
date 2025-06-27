<template>
  <div class="anime-card" @click="$emit('click')">
    <!-- 番剧封面 -->
    <div class="card-image">
      <img 
        v-if="props.shouldLoadImage"
        :src="props.anime.images.large" 
        :alt="props.anime.name_cn || props.anime.name"
        @error="onImageError"
        @load="$emit('imageLoad')"
      />
      <div v-else class="image-placeholder">
        <div class="loading-text">加载中...</div>
      </div>
      <div class="rating-badge" v-if="props.anime.rating && props.anime.rating.score > 0">
        {{ props.anime.rating.score.toFixed(1) }}
      </div>
    </div>

    <!-- 番剧信息 -->
    <div class="card-content">
      <h3 class="anime-title">
        {{ anime.name_cn || anime.name }}
      </h3>
      <p class="anime-subtitle" v-if="anime.name_cn && anime.name !== anime.name_cn">
        {{ anime.name }}
      </p>
      <div class="anime-meta">
        <span class="air-date">{{ formatAirDate(anime.air_date) }}</span>
        <span class="rating-count" v-if="anime.rating && anime.rating.total > 0">
          {{ anime.rating.total }}人评价
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BangumiCalendarItem } from '../services/api'

// Props定义
const props = withDefaults(defineProps<{
  anime: BangumiCalendarItem
  shouldLoadImage?: boolean
}>(), {
  shouldLoadImage: true
})

// Events定义
defineEmits<{
  click: []
  imageLoad: []
}>()

// 格式化播出日期
const formatAirDate = (dateStr: string): string => {
  if (!dateStr) return '未知'
  
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch {
    return dateStr
  }
}

// 图片加载失败处理
const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.anime-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-image {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;  /* 保持3:4的标准动漫封面比例 */
  overflow: hidden;
  background-color: #f8f9fa;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;  /* 从顶部中心开始显示，保留更多重要内容 */
  transition: transform 0.3s ease;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  color: #6c757d;
  font-size: 0.9rem;
}

.anime-card:hover .card-image img {
  transform: scale(1.05);
}

.rating-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(52, 152, 219, 0.9);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.card-content {
  padding: 0.875rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.anime-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.anime-subtitle {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-bottom: 0.5rem;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.anime-meta {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #95a5a6;
}

.air-date {
  font-weight: 500;
}

.rating-count {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-content {
    padding: 0.75rem;
  }
  
  .anime-title {
    font-size: 1rem;
  }
}
</style> 