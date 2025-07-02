<template>
  <div class="episode-carousel-container">
    <h3 class="section-title">章节列表</h3>

    <!-- 集数统计信息 -->
    <div v-if="!loading && !error && episodeStats" class="episode-stats">
      <span class="stats-text">
        共{{ totalEpisodes }}章节，已有{{ episodeStats.availableCount }}章节
      </span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>正在加载章节信息...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadEpisodeData" class="retry-btn">重试</button>
    </div>

    <!-- 横向滑动卡片 -->
    <div v-else-if="episodes.length > 0" class="carousel-wrapper">
      <div class="episode-carousel" ref="carouselContainer">
        <div
          v-for="episode in episodes"
          :key="episode.number"
          :class="[
            'episode-card',
            episode.available ? 'available' : 'unavailable'
          ]"
          @click="handleEpisodeClick(episode)"
        >
          <!-- 集数编号 -->
          <div class="episode-number">
            <span class="number">{{ String(episode.number).padStart(2, '0') }}</span>
          </div>

          <!-- 集数信息 -->
          <div class="episode-info">
            <h4 class="episode-title">{{ episode.title || `第${episode.number}集` }}</h4>
            <p class="episode-subtitle" v-if="episode.subtitle">{{ episode.subtitle }}</p>

            <div class="episode-meta">
              <span v-if="episode.duration" class="duration">时长: {{ episode.duration }}</span>
              <span v-if="episode.airdate" class="airdate">首播: {{ formatDate(episode.airdate) }}</span>
            </div>
          </div>

          <!-- 资源状态 -->
          <div class="resource-status">
            <div v-if="episode.available" class="has-resources">
              <span class="resource-count">{{ episode.resourceCount }}个资源</span>
              <button class="download-btn">下载</button>
            </div>
            <div v-else class="no-resources">
              <span class="no-resource-text">暂无资源</span>
              <button class="refresh-btn">刷新</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 滑动控制 -->
      <div class="carousel-controls">
        <button
          @click="scrollLeft"
          :disabled="isAtStart"
          class="control-btn prev-btn"
        >
          ←
        </button>
        <button
          @click="scrollRight"
          :disabled="isAtEnd"
          class="control-btn next-btn"
        >
          →
        </button>
      </div>
    </div>

    <!-- 无数据状态 -->
    <div v-else class="no-data-state">
      <p>暂无集数信息</p>
    </div>

    <!-- 章节详情模态框 -->
    <EpisodeDetailModal
      :visible="modalVisible"
      :episode-data="selectedEpisode"
      :bangumi-id="bangumiId"
      @close="closeModal"
      @refresh-resources="handleRefreshResources"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import BangumiApiService, { type EpisodeAvailabilityData, type BangumiEpisode } from '../services/api'
import EpisodeDetailModal from './EpisodeDetailModal.vue'

// Props定义
interface Props {
  bangumiId: number
  totalEpisodes: number
  bangumiEpisodes?: BangumiEpisode[]
  episodeStats?: any
  preloadedAvailability?: EpisodeAvailabilityData
}

const props = defineProps<Props>()

// 集数详细信息类型（现在使用真实Bangumi数据）
interface EpisodeDetail {
  number: number
  title: string          // 集数标题
  subtitle?: string      // 副标题或原文标题
  duration?: string      // 时长
  airdate?: string       // 播出日期
  desc?: string         // 集数描述
  comment?: number      // 评论数
  available: boolean    // 是否有资源
  resourceCount: number // 资源数量
  bangumiData?: BangumiEpisode  // 完整的Bangumi数据
}

// 响应式数据
const loading = ref(true)
const error = ref<string | null>(null)
const availabilityData = ref<EpisodeAvailabilityData | null>(null)
const carouselContainer = ref<HTMLElement>()
const isAtStart = ref(true)
const isAtEnd = ref(false)

// 模态框相关状态
const modalVisible = ref(false)
const selectedEpisode = ref<EpisodeDetail | null>(null)

// 计算属性 - 集数列表（现在使用真实Bangumi数据）
const episodes = computed((): EpisodeDetail[] => {
  const episodeList: EpisodeDetail[] = []

  // 如果有Bangumi数据，优先使用
  if (props.bangumiEpisodes && props.bangumiEpisodes.length > 0) {
    props.bangumiEpisodes.forEach((bangumiEp) => {
      const episodeKey = Math.floor(bangumiEp.sort || bangumiEp.ep || 0).toString()
      const episodeData = availabilityData.value?.episodes[episodeKey]

      episodeList.push({
        number: Math.floor(bangumiEp.sort || bangumiEp.ep || 0),
        title: bangumiEp.name_cn || bangumiEp.name || `第${Math.floor(bangumiEp.sort)}集`,
        subtitle: bangumiEp.name_cn ? bangumiEp.name : undefined,
        duration: bangumiEp.duration || undefined,
        airdate: bangumiEp.airdate || undefined,
        desc: bangumiEp.desc || undefined,
        comment: bangumiEp.comment || 0,
        available: episodeData?.available || false,
        resourceCount: episodeData?.resource_count || 0,
        bangumiData: bangumiEp
      })
    })

    // 按集数排序
    episodeList.sort((a, b) => a.number - b.number)
  } else {
    // 回退到原有的模拟数据逻辑
    for (let i = 1; i <= props.totalEpisodes; i++) {
      const episodeKey = i.toString()
      const episodeData = availabilityData.value?.episodes[episodeKey]

      episodeList.push({
        number: i,
        title: `第${i}集`,
        subtitle: undefined,
        duration: '24:00',
        airdate: undefined,
        desc: undefined,
        comment: Math.floor(Math.random() * 20),
        available: episodeData?.available || false,
        resourceCount: episodeData?.resource_count || 0
      })
    }
  }

  return episodeList
})

// 计算属性 - 集数统计
const episodeStats = computed(() => {
  if (!availabilityData.value) return null

  const availableCount = episodes.value.filter(ep => ep.available).length
  return {
    totalCount: props.totalEpisodes,
    availableCount
  }
})

// 加载集数数据
const loadEpisodeData = async () => {
  try {
    loading.value = true
    error.value = null

    // 先获取资源可用性
    const data = await BangumiApiService.getEpisodeAvailability(props.bangumiId)
    availabilityData.value = data

    // TODO: 未来在这里添加获取详细集数信息的API调用
    // const episodeDetails = await BangumiApiService.getEpisodeDetails(props.bangumiId)

  } catch (err) {
    console.error('加载集数信息失败:', err)
    error.value = '加载集数信息失败，请检查网络连接'
  } finally {
    loading.value = false
    nextTick(() => {
      updateScrollButtons()
    })
  }
}

// 处理集数点击
const handleEpisodeClick = (episode: EpisodeDetail) => {
  selectedEpisode.value = episode
  modalVisible.value = true
}

// 关闭模态框
const closeModal = () => {
  modalVisible.value = false
  selectedEpisode.value = null
}

// 处理刷新资源
const handleRefreshResources = async (episodeNumber: number) => {
  // TODO: 实现刷新特定集数资源的逻辑
  try {
    // 重新加载该集数的资源信息
    await loadEpisodeAvailability()
  } catch (err) {
    console.error('刷新资源失败:', err)
  }
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

// 截断描述文字
const truncateDesc = (desc: string): string => {
  if (!desc) return ''
  return desc.length > 60 ? desc.substring(0, 60) + '...' : desc
}

// 滑动控制
const scrollLeft = () => {
  if (carouselContainer.value) {
    carouselContainer.value.scrollBy({ left: -320, behavior: 'smooth' })
    setTimeout(updateScrollButtons, 300)
  }
}

const scrollRight = () => {
  if (carouselContainer.value) {
    carouselContainer.value.scrollBy({ left: 320, behavior: 'smooth' })
    setTimeout(updateScrollButtons, 300)
  }
}

const updateScrollButtons = () => {
  if (carouselContainer.value) {
    const container = carouselContainer.value
    isAtStart.value = container.scrollLeft === 0
    isAtEnd.value = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1
  }
}

// 组件挂载时加载数据
onMounted(() => {
  if (props.bangumiId && props.totalEpisodes > 0) {
    // 如果有预加载的资源可用性数据，直接使用（包括null值，表示资源API失败）
    if (props.preloadedAvailability !== undefined) {
      availabilityData.value = props.preloadedAvailability
      loading.value = false
      nextTick(() => {
        updateScrollButtons()
      })
    }
    // 如果已有Bangumi章节数据，只加载资源可用性
    else if (props.bangumiEpisodes && props.bangumiEpisodes.length > 0) {
      loadEpisodeAvailability()
    } else {
      loadEpisodeData()
    }
  } else {
    error.value = '无效的番剧信息'
    loading.value = false
  }
})

// 单独加载资源可用性的函数
const loadEpisodeAvailability = async () => {
  try {
    loading.value = true
    error.value = null

    // 只获取资源可用性
    const data = await BangumiApiService.getEpisodeAvailability(props.bangumiId)
    availabilityData.value = data

  } catch (err) {
    console.error('加载资源可用性失败:', err)
    error.value = '加载资源信息失败，请检查网络连接'
  } finally {
    loading.value = false
    nextTick(() => {
      updateScrollButtons()
    })
  }
}
</script>

<style scoped>
.episode-carousel-container {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.episode-stats {
  margin-bottom: 1.5rem;
}

.stats-text {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.loading-state, .error-state, .no-data-state {
  text-align: center;
  padding: 2rem;
  color: #7f8c8d;
}

.error-state {
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

.carousel-wrapper {
  position: relative;
}

.episode-carousel {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding-bottom: 1rem;
  scrollbar-width: thin;
}

.episode-carousel::-webkit-scrollbar {
  height: 6px;
}

.episode-carousel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.episode-carousel::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.episode-carousel::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.episode-card {
  flex: 0 0 300px;
  height: 200px;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.episode-card.available {
  background: linear-gradient(135deg, #D34642 0%, #B73B3B 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(183, 59, 59, 0.3);
  position: relative;
}

.episode-card.available::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  pointer-events: none;
  z-index: -1;
}

.episode-card.unavailable {
  background: linear-gradient(135deg, #F5B5B3 0%, #E87572 100%);
  color: #2d3436;
  opacity: 0.8;
  box-shadow: 0 4px 12px rgba(232, 117, 114, 0.3);
}

.episode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.episode-number {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1;
}

.number {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: bold;
  font-size: 0.9rem;
}

.episode-info {
  flex: 1;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
  margin-right: 60px;
}

.episode-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 70px;
}

.episode-subtitle {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-bottom: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 70px;
}

.episode-meta {
  display: flex;
  flex-direction: row;
  gap: 1rem;
  font-size: 0.8rem;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}



.resource-status {
  margin-top: auto;
  padding-top: 0.5rem;
  position: relative;
  z-index: 1;
}

.has-resources, .no-resources {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-count, .no-resource-text {
  font-size: 0.85rem;
  font-weight: 500;
}

.download-btn, .refresh-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  color: inherit;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.download-btn:hover, .refresh-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.carousel-controls {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
  padding: 0 -1rem;
}

.control-btn {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: #2c3e50;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
  pointer-events: auto;
}

.control-btn:hover:not(:disabled) {
  background: white;
  transform: scale(1.1);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .episode-carousel-container {
    padding: 1.5rem;
  }

  .episode-card {
    flex: 0 0 250px;
    height: 180px;
  }

  .carousel-controls {
    display: none; /* 移动端隐藏控制按钮，使用触摸滑动 */
  }
}

@media (max-width: 480px) {
  .episode-card {
    flex: 0 0 220px;
    height: 160px;
    padding: 0.75rem;
  }

  .episode-title {
    font-size: 1rem;
  }

  .episode-meta {
    font-size: 0.75rem;
  }
}
</style>
