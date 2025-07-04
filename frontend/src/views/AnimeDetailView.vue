<template>
  <div class="anime-detail">
    <!-- 返回按钮 -->
    <div class="navigation">
      <button @click="goBack" class="back-btn">
        ← 返回
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在加载番剧详情...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="() => animeDetailStore.fetchAll(animeId)" class="retry-btn">重试</button>
    </div>

    <!-- 番剧详情内容 -->
    <div v-else-if="subject" class="detail-container">
      <!-- 番剧基本信息 -->
      <div class="anime-header">
        <div class="anime-cover">
          <img
            :src="subject.images.large"
            :alt="subject.name_cn || subject.name"
            @error="onImageError"
          />
        </div>

        <div class="anime-info">
          <h1 class="anime-title">{{ subject.name_cn || subject.name }}</h1>
          <h2 v-if="subject.name_cn && subject.name !== subject.name_cn" class="anime-subtitle">
            {{ subject.name }}
          </h2>

          <div class="anime-meta">
            <div class="meta-item">
              <span class="meta-label">播出日期:</span>
              <span class="meta-value">{{ formatAirDate(subject.date) }}</span>
            </div>
            <div class="meta-item" v-if="subject.eps">
              <span class="meta-label">总集数:</span>
              <span class="meta-value">{{ subject.eps }}集</span>
            </div>
            <div class="meta-item" v-if="subject.rating.score > 0">
              <span class="meta-label">评分:</span>
              <span class="meta-value rating">
                {{ subject.rating.score.toFixed(1) }}
                <span class="rating-total">({{ subject.rating.total }}人评价)</span>
              </span>
            </div>
            <div class="meta-item" v-if="subject.rank">
              <span class="meta-label">排名:</span>
              <span class="meta-value">#{{ subject.rank }}</span>
            </div>
          </div>

          <!-- 动画标签 -->
          <div class="anime-tags" v-if="subject.tags && subject.tags.length > 0">
            <div class="tags-container">
              <span
                v-for="tag in getTopTags(subject.tags)"
                :key="tag.name"
                class="tag-item"
                :class="getTagType(tag.name)"
              >
                {{ tag.name }}
                <span class="tag-count">{{ tag.count }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 番剧简介 -->
      <div class="anime-summary" v-if="subject.summary">
        <h3>简介</h3>
        <p>{{ subject.summary }}</p>
      </div>

      <!-- 追番模式：章节信息 -->
      <EpisodeDisplay
        v-if="!isResourceMode && (subject.total_episodes > 0 || subject.eps > 0)"
        :bangumi-id="animeId"
      />

      <!-- 资源库模式：资源列表 -->
      <AnimeResourcesList
        v-if="isResourceMode"
        :bangumi-id="animeId"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAnimeDetailStore } from '../stores/animeDetailStore'
import { useResourceStore } from '../stores/resourceStore'
import { useEpisodeAvailabilityStore } from '../stores/episodeAvailabilityStore'
import { ensureScrollToTop } from '../utils/scrollUtils'
import EpisodeDisplay from '../components/EpisodeDisplay.vue'
import AnimeResourcesList from '../components/AnimeResourcesList.vue'

const route = useRoute()
const router = useRouter()
const animeDetailStore = useAnimeDetailStore()
const resourceStore = useResourceStore()
const episodeAvailabilityStore = useEpisodeAvailabilityStore()
const { subject, episodes, availability, loading, error } = storeToRefs(animeDetailStore)

// 获取番剧ID
const animeId = computed(() => parseInt(route.params.id as string))

// 判断是否为资源库模式
const isResourceMode = route.meta.showResources === true

// 页面加载时拉取数据
onMounted(() => {
  ensureScrollToTop()
  if (animeId.value) {
    animeDetailStore.fetchAll(animeId.value)
    // 资源拉取已由AnimeResourcesList.vue负责，这里无需再调用resourceStore.fetchResources
  }
})

// 监听animeId变化，自动拉取数据
watch(animeId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    animeDetailStore.fetchAll(newId)
    // 资源拉取已由AnimeResourcesList.vue负责，这里无需再调用resourceStore.fetchResources
  }
})

// 页面卸载时清空store（只在真正卸载时清理，避免keep-alive下丢失）
onBeforeUnmount(() => {
  animeDetailStore.clear()
  if (isResourceMode) {
    resourceStore.clear()
  } else {
    episodeAvailabilityStore.clear()
  }
})

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 格式化播出日期
const formatAirDate = (dateStr: string): string => {
  if (!dateStr) return '未知'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateStr
  }
}

// 获取前15个热门标签
const getTopTags = (tags: any[]) => {
  return tags
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)
}

// 根据标签名称返回标签类型（用于样式）
const getTagType = (tagName: string): string => {
  if ([
    'TV', 'TV动画', 'OVA', 'OAD', '电影', '特别篇'
  ].includes(tagName)) return 'tag-media'
  if ([
    '恋爱', '治愈', '奇幻', '科幻', '日常', '冒险', '悬疑', '战斗', '搞笑'
  ].includes(tagName)) return 'tag-genre'
  if (tagName.includes('改') || tagName.includes('GAL') || tagName.includes('游戏') || tagName.includes('小说') || tagName.includes('漫画')) return 'tag-source'
  if (tagName.includes('年') || tagName.includes('月') || /^[A-Z][a-z]*\.?$/.test(tagName)) return 'tag-production'
  return 'tag-default'
}

// 图片加载失败处理
const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.anime-detail {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
}

.navigation {
  margin-bottom: 2rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.back-btn:hover {
  background-color: #2980b9;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
}

.error {
  color: #e74c3c;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-btn:hover {
  background-color: #2980b9;
}

.detail-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.anime-header {
  display: flex;
  gap: 2rem;
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.anime-cover {
  flex-shrink: 0;
}

.anime-cover img {
  width: 240px;
  height: 320px;
  object-fit: cover;
  border-radius: 8px;
}

.anime-info {
  flex: 1;
}

.anime-title {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.anime-subtitle {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin-bottom: 1.5rem;
  font-weight: normal;
}

.anime-meta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
}

.meta-label {
  font-weight: 600;
  color: #34495e;
  width: 80px;
  flex-shrink: 0;
}

.meta-value {
  color: #2c3e50;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #f39c12;
}

.rating-total {
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: normal;
}

.anime-tags {
  margin-top: 1.5rem;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: default;
}

.tag-count {
  background: rgba(255, 255, 255, 0.3);
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

/* 不同类型标签的颜色 */
.tag-media {
  background: linear-gradient(45deg, #3498db, #2980b9);
  color: white;
}

.tag-genre {
  background: linear-gradient(45deg, #e74c3c, #c0392b);
  color: white;
}

.tag-source {
  background: linear-gradient(45deg, #f39c12, #e67e22);
  color: white;
}

.tag-production {
  background: linear-gradient(45deg, #9b59b6, #8e44ad);
  color: white;
}

.tag-default {
  background-color: #f0f0f0;
  color: #666;
}

.tag-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.anime-summary {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.anime-summary h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.anime-summary p {
  line-height: 1.6;
  color: #34495e;
}

.resources-section {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.resources-section h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.resources-notice {
  color: #7f8c8d;
  font-style: italic;
  text-align: center;
  padding: 2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .anime-detail {
    padding: 1rem;
  }

  .anime-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .anime-cover img {
    width: 200px;
    height: 267px;
  }

  .anime-title {
    font-size: 1.5rem;
  }

  .anime-meta {
    align-items: center;
  }

  .meta-item {
    justify-content: center;
  }

  .tags-container {
    justify-content: center;
  }
}
</style>
