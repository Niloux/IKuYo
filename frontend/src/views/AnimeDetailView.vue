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
      <button @click="loadAnimeDetail" class="retry-btn">重试</button>
    </div>

    <!-- 番剧详情内容 -->
    <div v-else-if="anime" class="detail-container">
      <!-- 番剧基本信息 -->
      <div class="anime-header">
        <div class="anime-cover">
          <img 
            :src="anime.images.large" 
            :alt="anime.name_cn || anime.name"
            @error="onImageError"
          />
        </div>
        
        <div class="anime-info">
          <h1 class="anime-title">{{ anime.name_cn || anime.name }}</h1>
          <h2 v-if="anime.name_cn && anime.name !== anime.name_cn" class="anime-subtitle">
            {{ anime.name }}
          </h2>
          
          <div class="anime-meta">
            <div class="meta-item">
              <span class="meta-label">播出日期:</span>
              <span class="meta-value">{{ formatAirDate(anime.date) }}</span>
            </div>
            <div class="meta-item" v-if="anime.eps">
              <span class="meta-label">总集数:</span>
              <span class="meta-value">{{ anime.eps }}集</span>
            </div>
            <div class="meta-item" v-if="anime.rating.score > 0">
              <span class="meta-label">评分:</span>
              <span class="meta-value rating">
                {{ anime.rating.score.toFixed(1) }}
                <span class="rating-total">({{ anime.rating.total }}人评价)</span>
              </span>
            </div>
            <div class="meta-item" v-if="anime.rank">
              <span class="meta-label">排名:</span>
              <span class="meta-value">#{{ anime.rank }}</span>
            </div>
          </div>

          <!-- 动画标签 -->
          <div class="anime-tags" v-if="anime.tags && anime.tags.length > 0">
            <div class="tags-container">
              <span 
                v-for="tag in getTopTags(anime.tags)" 
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
      <div class="anime-summary" v-if="anime.summary">
        <h3>简介</h3>
        <p>{{ anime.summary }}</p>
      </div>

      <!-- 评分分布 -->
      <div class="rating-distribution" v-if="anime.rating.count">
        <h3>评分分布</h3>
        <div class="rating-bars">
          <div 
            v-for="(count, score) in anime.rating.count" 
            :key="score"
            class="rating-bar"
          >
            <span class="score-label">{{ score }}分</span>
            <div class="bar-container">
              <div 
                class="bar-fill" 
                :style="{ width: getBarWidth(count, anime.rating.total) + '%' }"
              ></div>
            </div>
            <span class="count-label">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- 智能集数展示 -->
      <EpisodeDisplay 
        v-if="anime.eps > 0"
        :bangumi-id="animeId"
        :show-debug-info="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BangumiApiService, { type BangumiSubject } from '../services/api'
import EpisodeDisplay from '../components/EpisodeDisplay.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const anime = ref<BangumiSubject | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// 获取番剧ID
const animeId = parseInt(route.params.id as string)

// 并行加载所有数据
const loadAnimeDetail = async () => {
  try {
    loading.value = true
    error.value = null
    
    console.log('🚀 开始并行加载番剧数据...')
    const startTime = performance.now()
    
    // 并行执行所有API调用
    const [subjectData] = await Promise.all([
      BangumiApiService.getSubject(animeId)
    ])
    
    anime.value = subjectData
    
    const loadTime = performance.now() - startTime
    console.log(`✅ 番剧基本信息加载完成，耗时: ${loadTime.toFixed(2)}ms`)
    
  } catch (err) {
    console.error('加载番剧详情失败:', err)
    error.value = '加载失败，请检查网络连接或API服务状态'
  } finally {
    loading.value = false
  }
}

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

// 计算评分条宽度
const getBarWidth = (count: number, total: number): number => {
  return total > 0 ? (count / total) * 100 : 0
}

// 获取前15个热门标签
const getTopTags = (tags: any[]) => {
  return tags
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)
}

// 根据标签名称返回标签类型（用于样式）
const getTagType = (tagName: string): string => {
  // 媒体类型标签
  if (['TV', 'TV动画', 'OVA', 'OAD', '电影', '特别篇'].includes(tagName)) {
    return 'tag-media'
  }
  // 题材类型标签
  if (['恋爱', '治愈', '奇幻', '科幻', '日常', '冒险', '悬疑', '战斗', '搞笑'].includes(tagName)) {
    return 'tag-genre'
  }
  // 改编类型标签
  if (tagName.includes('改') || tagName.includes('GAL') || tagName.includes('游戏') || tagName.includes('小说') || tagName.includes('漫画')) {
    return 'tag-source'
  }
  // 制作相关标签
  if (tagName.includes('年') || tagName.includes('月') || /^[A-Z][a-z]*\.?$/.test(tagName)) {
    return 'tag-production'
  }
  // 默认标签
  return 'tag-default'
}

// 图片加载失败处理
const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// 组件挂载时加载数据
onMounted(() => {
  if (animeId) {
    loadAnimeDetail()
  } else {
    error.value = '无效的番剧ID'
    loading.value = false
  }
})
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
  background: linear-gradient(45deg, #95a5a6, #7f8c8d);
  color: white;
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

.rating-distribution {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rating-distribution h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.rating-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rating-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.score-label {
  width: 40px;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.bar-container {
  flex: 1;
  height: 20px;
  background-color: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background-color: #3498db;
  transition: width 0.3s ease;
}

.count-label {
  width: 50px;
  text-align: right;
  font-size: 0.9rem;
  color: #7f8c8d;
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