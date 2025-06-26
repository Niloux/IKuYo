<template>
  <div class="episode-grid-container">
    <h3 class="section-title">章节信息</h3>
    
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
      <button @click="loadEpisodeAvailability" class="retry-btn">重试</button>
    </div>

    <!-- 集数网格 -->
    <div v-else-if="episodes.length > 0" class="episode-grid" :style="gridStyle">
      <div
        v-for="episode in episodes"
        :key="episode.number"
        :class="[
          'episode-item', 
          episode.available ? 'available' : 'unavailable'
        ]"
        @click="handleEpisodeClick(episode)"
        :title="episode.available ? `第${episode.number}集 (${episode.resourceCount}个资源)` : `第${episode.number}集 (暂无资源)`"
      >
        {{ episode.number }}
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
  preloadedAvailability?: EpisodeAvailabilityData
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(true)
const error = ref<string | null>(null)
const availabilityData = ref<EpisodeAvailabilityData | null>(null)

// 计算属性 - 集数列表
const episodes = computed(() => {
  const episodeList = []
  
  for (let i = 1; i <= props.totalEpisodes; i++) {
    const episodeKey = i.toString()
    const episodeData = availabilityData.value?.episodes[episodeKey]
    
    episodeList.push({
      number: i,
      available: episodeData?.available || false,
      resourceCount: episodeData?.resource_count || 0
    })
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
  const totalEps = props.totalEpisodes
  
  // 如果集数少于17，使用固定尺寸；如果达到17集，则充满宽度
  if (totalEps < 17) {
    return {
      gridTemplateColumns: `repeat(${columns}, 36px)`,
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
    // 如果有预加载的资源可用性数据，直接使用
    if (props.preloadedAvailability) {
      console.log('⚡ 使用预加载的资源可用性数据，无需额外API调用')
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

/* 响应式设计 */
@media (max-width: 768px) {
  .episode-grid-container {
    padding: 1.5rem;
  }
  
  .episode-item {
    min-height: 28px;
    font-size: 0.75rem;
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
}
</style> 