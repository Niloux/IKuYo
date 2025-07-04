<template>
  <div class="anime-card" @click="handleCardClick" ref="cardRef">
    <!-- 番剧封面 -->
    <div class="card-image">
      <img
        v-if="shouldLoadImage"
        :src="imageUrl"
        :alt="props.anime.name_cn || props.anime.name"
        @error="onImageError"
        @load="$emit('imageLoad')"
      />
      <Skeleton v-else type="image" customClass="anime-card-skeleton" />
      <div class="rating-badge" v-if="props.anime.rating && props.anime.rating.score > 0">
        {{ props.anime.rating.score.toFixed(1) }}
      </div>

      <!-- 订阅按钮 -->
      <button
        v-if="props.showSubscriptionButton"
        @click.stop="handleSubscriptionToggle"
        class="subscription-btn"
        :class="{ subscribed: isSubscribed }"
        :disabled="subscriptionLoading"
        :title="isSubscribed ? '取消订阅' : '订阅'"
      >
        <span v-if="subscriptionLoading">⏳</span>
        <span v-else>
          <!-- Material Design标准心形icon -->
          <svg v-if="!isSubscribed" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e50914" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16.5 3c-1.74 0-3.41 1.01-4.5 2.09C10.91 4.01 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54a2 2 0 0 0 2.9 0C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/>
          </svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="#e50914" stroke="#e50914" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16.5 3c-1.74 0-3.41 1.01-4.5 2.09C10.91 4.01 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54a2 2 0 0 0 2.9 0C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/>
          </svg>
        </span>
      </button>
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
import { ref, computed, onMounted, onUnmounted, withDefaults, defineProps } from 'vue'
import type { BangumiCalendarItem } from '../services/bangumi/bangumiTypes'
import defaultCover from '../assets/ikuyo-avatar.png'
import { createLazyObserver } from '../utils/lazyLoad'
import Skeleton from './common/Skeleton.vue'
import { useSubscriptionStore } from '../stores/subscriptionStore'
import { useFeedbackStore } from '../stores/feedbackStore'

// Props定义（修正默认值）
const props = withDefaults(defineProps<{
  anime: BangumiCalendarItem
  showSubscriptionButton?: boolean
}>(), {
  showSubscriptionButton: true
})

// Events定义
const emit = defineEmits<{
  click: []
  imageLoad: []
}>()

// 懒加载本地状态
const shouldLoadImage = ref(false)
const cardRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

// 订阅功能
const subscriptionStore = useSubscriptionStore()
const subscriptionLoading = ref(false)

// 检查是否已订阅
const isSubscribed = computed(() => {
  return subscriptionStore.isSubscribed(props.anime.id)
})

// 处理订阅状态切换
const handleSubscriptionToggle = async () => {
  try {
    subscriptionLoading.value = true
    await subscriptionStore.toggleSubscription(props.anime)
  } catch (error) {
    const feedbackStore = useFeedbackStore();
    feedbackStore.showError('订阅操作失败，请重试')
    console.error('订阅操作失败:', error)
  } finally {
    subscriptionLoading.value = false
  }
}

onMounted(() => {
  if (cardRef.value) {
    observer = createLazyObserver(cardRef.value, () => {
      shouldLoadImage.value = true
    })
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})

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

// 将HTTP URL转换为HTTPS（修复CORS问题）
const convertToHttps = (url: string): string => {
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://')
  }
  return url
}

// 获取HTTPS图片URL
const imageUrl = computed(() => {
  const imgObj = props.anime.images
  if (imgObj && imgObj.large) {
    return convertToHttps(imgObj.large)
  }
  return defaultCover
})

// 图片加载失败处理
const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = defaultCover
}

const handleCardClick = () => {
  emit('click')
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

.subscription-btn {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.92);
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: transform 0.18s cubic-bezier(.4,1.3,.6,1), box-shadow 0.18s;
  padding: 0;
}

.subscription-btn:hover:not(:disabled) {
  transform: scale(1.12);
  box-shadow: 0 4px 16px rgba(229,9,20,0.18);
}

.subscription-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.subscription-btn svg {
  display: block;
}

.subscription-btn.subscribed {
  background: rgba(229,9,20,0.10);
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
