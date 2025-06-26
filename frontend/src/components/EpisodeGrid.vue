<template>
  <div class="episode-grid-container">
    <h3 class="section-title">章节信息</h3>
    
    <!-- 集数统计信息 -->
    <div v-if="!loading && !error && episodeStats" class="episode-stats">
      <span class="stats-text">
        共{{ actualTotalEpisodes }}章节，已有{{ episodeStats.availableCount }}章节
        <template v-if="needsPagination && currentPageRange">
          (第{{ currentPageRange.start }}-{{ currentPageRange.end }}集，当前页{{ episodeStats.currentPageAvailableCount }}章节)
        </template>
      </span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>正在加载章节信息...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadEpisodeAvailability" class="retry-btn">重试</button>
    </div>

    <!-- 集数网格 -->
    <div v-else-if="currentPageEpisodes.length > 0" class="episode-grid" :style="gridStyle">
      <div
        v-for="episode in currentPageEpisodes"
        :key="episode.number"
        :class="[
          'episode-item', 
          episode.available ? 'available' : 'unavailable'
        ]"
        @click="handleEpisodeClick(episode)"
        :title="episode.available ? `${episode.title} (${episode.resourceCount}个资源)` : `${episode.title} (暂无资源)`"
      >
        {{ episode.number }}
      </div>
    </div>

    <!-- 分页控件 -->
    <div v-if="needsPagination" class="pagination-container">
      <div class="pagination-info">
        <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
      </div>
      
      <div class="pagination-controls">
        <button 
          @click="goToPrevPage" 
          :disabled="currentPage === 1"
          class="pagination-btn prev-btn"
        >
          上一页
        </button>
        
        <div class="page-numbers">
          <!-- 首页 -->
          <button 
            v-if="currentPage > 3"
            @click="goToPage(1)"
            class="pagination-btn page-btn"
          >
            1
          </button>
          
          <!-- 省略号 -->
          <span v-if="currentPage > 4" class="pagination-ellipsis">...</span>
          
          <!-- 当前页附近的页码 -->
          <button
            v-for="page in getVisiblePages()"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'pagination-btn', 'page-btn',
              { 'active': page === currentPage }
            ]"
          >
            {{ page }}
          </button>
          
          <!-- 省略号 -->
          <span v-if="currentPage < totalPages - 3" class="pagination-ellipsis">...</span>
          
          <!-- 尾页 -->
          <button 
            v-if="currentPage < totalPages - 2"
            @click="goToPage(totalPages)"
            class="pagination-btn page-btn"
          >
            {{ totalPages }}
          </button>
        </div>
        
        <button 
          @click="goToNextPage" 
          :disabled="currentPage === totalPages"
          class="pagination-btn next-btn"
        >
          下一页
        </button>
      </div>
      
      <!-- 快速跳转 -->
      <div class="pagination-jump">
        <span>跳转到</span>
        <input 
          type="number" 
          :min="1" 
          :max="totalPages"
          v-model.number="jumpPage"
          @keyup.enter="handleJumpToPage"
          class="jump-input"
        />
        <button @click="handleJumpToPage" class="pagination-btn jump-btn">确定</button>
      </div>
    </div>

    <!-- 无数据状态 -->
    <div v-else class="no-data-state">
      <p>暂无集数信息</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import BangumiApiService, { type EpisodeAvailabilityData } from '../services/api'

// Props定义
interface Props {
  bangumiId: number
  totalEpisodes: number
  bangumiEpisodes?: any[]  // Bangumi集数数据
  preloadedAvailability?: EpisodeAvailabilityData
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(true)
const error = ref<string | null>(null)
const availabilityData = ref<EpisodeAvailabilityData | null>(null)

// 分页相关状态
const currentPage = ref(1)
const episodesPerPage = 85 // 5行 × 17列
const jumpPage = ref<number>(1)

// 计算属性 - 集数列表
const episodes = computed(() => {
  const episodeList = []
  
  // 创建Bangumi数据的映射表
  const bangumiMap = new Map()
  if (props.bangumiEpisodes && props.bangumiEpisodes.length > 0) {
    props.bangumiEpisodes
      .filter(ep => ep.type === 0) // 只处理正片
      .forEach(bangumiEp => {
        const episodeNumber = Math.floor(bangumiEp.sort || bangumiEp.ep || 0)
        bangumiMap.set(episodeNumber, bangumiEp)
      })
  }
  
  // 基于totalEpisodes生成完整列表，并尽可能使用真实Bangumi数据
  for (let i = 1; i <= props.totalEpisodes; i++) {
    const episodeKey = i.toString()
    const episodeData = availabilityData.value?.episodes[episodeKey]
    const bangumiEp = bangumiMap.get(i)
    
    episodeList.push({
      number: i,
      available: episodeData?.available || false,
      resourceCount: episodeData?.resource_count || 0,
      title: bangumiEp ? (bangumiEp.name_cn || bangumiEp.name || `第${i}集`) : `第${i}集`,
      bangumiData: bangumiEp || null
    })
  }
  
  return episodeList
})

// 计算属性 - 实际集数总数（使用真实数据长度）
const actualTotalEpisodes = computed(() => episodes.value.length)

// 计算属性 - 分页相关
const needsPagination = computed(() => actualTotalEpisodes.value > episodesPerPage)
const totalPages = computed(() => Math.ceil(actualTotalEpisodes.value / episodesPerPage))

// 计算属性 - 当前页显示的集数
const currentPageEpisodes = computed(() => {
  if (!needsPagination.value) {
    return episodes.value
  }
  
  const startIndex = (currentPage.value - 1) * episodesPerPage
  const endIndex = Math.min(startIndex + episodesPerPage, actualTotalEpisodes.value)
  
  return episodes.value.slice(startIndex, endIndex)
})

// 计算属性 - 当前页范围信息
const currentPageRange = computed(() => {
  if (!needsPagination.value) return null
  
  const startEpisode = (currentPage.value - 1) * episodesPerPage + 1
  const endEpisode = Math.min(currentPage.value * episodesPerPage, actualTotalEpisodes.value)
  
  return { start: startEpisode, end: endEpisode }
})

// 计算属性 - 集数统计
const episodeStats = computed(() => {
  const availableCount = episodes.value.filter(ep => ep.available).length
  const currentPageAvailableCount = currentPageEpisodes.value.filter(ep => ep.available).length
  
  return {
    totalCount: actualTotalEpisodes.value,
    availableCount,
    currentPageAvailableCount
  }
})

// 计算属性 - 每行列数
const columnsPerRow = computed(() => {
  const totalEps = props.totalEpisodes
  
  // 根据集数总数确定每行显示的列数
  if (totalEps <= 10) return totalEps
  if (totalEps <= 17) return Math.min(17, totalEps)
  return 17
})

// 计算属性 - 网格样式
const gridStyle = computed(() => {
  const columns = columnsPerRow.value
  const currentPageEpsCount = currentPageEpisodes.value.length
  
  // 如果当前页集数少于17，使用固定尺寸；否则使用17列布局
  if (currentPageEpsCount < 17 && !needsPagination.value) {
    return {
      gridTemplateColumns: `repeat(${currentPageEpsCount}, 36px)`,
      gap: '6px',
      justifyContent: 'start'
    }
  } else {
    return {
      gridTemplateColumns: `repeat(${columns}, 1fr)`,
      gap: '6px'
    }
  }
})

// 加载集数可用性数据
const loadEpisodeAvailability = async () => {
  try {
    loading.value = true
    error.value = null
    
    const data = await BangumiApiService.getEpisodeAvailability(props.bangumiId)
    availabilityData.value = data
  } catch (err) {
    console.error('加载集数可用性失败:', err)
    error.value = '加载集数信息失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

// 分页控制方法
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const goToPrevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 获取可见的页码范围
const getVisiblePages = () => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
}

// 处理跳转到指定页
const handleJumpToPage = () => {
  const page = jumpPage.value
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 处理集数点击
const handleEpisodeClick = (episode: { number: number, available: boolean, resourceCount: number }) => {
  if (episode.available) {
    // 暂时显示提示信息，后续替换为路由跳转
    alert(`第${episode.number}集资源详情功能开发中...`)
  } else {
    alert(`第${episode.number}集暂无资源`)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  if (props.bangumiId && props.totalEpisodes > 0) {
    // 如果有预加载的资源可用性数据，直接使用（包括null值，表示资源API失败）
    if (props.preloadedAvailability !== undefined) {
      availabilityData.value = props.preloadedAvailability
      loading.value = false
    } else {
      loadEpisodeAvailability()
    }
  } else {
    error.value = '无效的番剧信息'
    loading.value = false
  }
})
</script>

<style scoped>
.episode-grid-container {
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

.episode-grid {
  display: grid;
  width: 100%;
}

.episode-item {
  aspect-ratio: 1;
  min-height: 28px;
  min-width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s ease;
  user-select: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.episode-item.available {
  background-color: #3498db;
  color: white;
  cursor: pointer;
}

.episode-item.available:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
}

.episode-item.unavailable {
  background-color: #ecf0f1;
  color: #bdc3c7;
  cursor: not-allowed;
}

/* 分页控件样式 */
.pagination-container {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e1e8ed;
}

.pagination-info {
  text-align: center;
  margin-bottom: 1rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pagination-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  min-width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #3498db;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn.active {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.pagination-ellipsis {
  padding: 0.5rem;
  color: #7f8c8d;
}

.pagination-jump {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.jump-input {
  width: 60px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
}

.jump-input:focus {
  outline: none;
  border-color: #3498db;
}

.jump-btn {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .episode-grid-container {
    padding: 1.5rem;
  }
  
  .episode-item {
    min-height: 28px;
    font-size: 0.75rem;
  }

  .pagination-controls {
    gap: 0.25rem;
  }

  .pagination-btn {
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
    min-width: 32px;
  }

  .pagination-jump {
    margin-top: 0.5rem;
    font-size: 0.8rem;
  }

  .jump-input {
    width: 50px;
  }
}

@media (max-width: 480px) {
  .episode-grid-container {
    padding: 1rem;
  }
  
  .episode-item {
    min-height: 24px;
    font-size: 0.7rem;
  }

  .pagination-container {
    margin-top: 1.5rem;
    padding-top: 1rem;
  }

  .pagination-controls {
    flex-direction: column;
    gap: 0.75rem;
  }

  .page-numbers {
    order: -1;
  }

  .pagination-jump {
    font-size: 0.75rem;
  }
}
</style> 