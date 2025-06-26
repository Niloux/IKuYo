<template>
    <div class="episode-display">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <p>正在加载章节信息...</p>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      
      <!-- 根据集数智能选择展示方式 -->
      <EpisodeCarousel 
        v-else-if="displayMode === 'carousel' && episodeStats"
        :bangumi-id="bangumiId"
        :total-episodes="episodeStats.main_episodes"
        :bangumi-episodes="bangumiEpisodes"
        :episode-stats="episodeStats"
        :preloaded-availability="episodeAvailability"
      />
      
      <EpisodeGrid 
        v-else-if="displayMode === 'grid' && episodeStats"
        :bangumi-id="bangumiId"
        :total-episodes="episodeStats.main_episodes"
        :bangumi-episodes="bangumiEpisodes"
        :preloaded-availability="episodeAvailability"
      />
      

    </div>
  </template>
  
  <script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import EpisodeCarousel from './EpisodeCarousel.vue'
  import EpisodeGrid from './EpisodeGrid.vue'
  import BangumiApiService, { type BangumiEpisode, type BangumiEpisodesStats } from '@/services/api'
  
  // Props定义
  interface Props {
    bangumiId: number
  }
  
  const props = defineProps<Props>()
  
  // 响应式数据
  const loading = ref(true)
  const error = ref<string | null>(null)
  const bangumiEpisodes = ref<BangumiEpisode[]>([])
  const episodeStats = ref<BangumiEpisodesStats | null>(null)
  const episodeAvailability = ref<any>(null)
  
  // 智能显示模式判断
  const MODERN_ANIME_THRESHOLD = 26
  
  const displayMode = computed(() => {
    if (!episodeStats.value) return 'carousel'
    return episodeStats.value.main_episodes <= MODERN_ANIME_THRESHOLD ? 'carousel' : 'grid'
  })
  

  
  // 获取Bangumi章节数据（核心API优先，资源API优雅降级）
  const fetchBangumiEpisodes = async () => {
    try {
      loading.value = true
      error.value = null
      
      // 先获取少量数据判断总集数，然后决定获取策略
      const initialData = await BangumiApiService.getBangumiEpisodes(props.bangumiId, 0, 50)
      
      let episodesData = initialData
      
      // 如果总集数超过50，使用最大limit获取完整数据
      if (initialData.total > 50) {
        const fullLimit = Math.min(initialData.total, 1000) // API最大限制1000
        episodesData = await BangumiApiService.getBangumiEpisodes(props.bangumiId, 0, fullLimit)
      }
      
      // 基于实际episodes数据计算统计信息（使用API返回的真实总数）
      const episodes = episodesData.data
      const actualMainEpisodes = episodes.filter(ep => ep.type === 0)
      
      const calculatedStats = {
        total: episodesData.total, // 使用API返回的真实总数，而不是获取的数据长度
        main_episodes: episodesData.total > 1000 
          ? episodesData.total // 如果总数超过1000，使用API报告的总数
          : actualMainEpisodes.length, // 否则使用实际获取的数据
        special_episodes: episodes.filter(ep => ep.type === 1).length,
        opening_episodes: episodes.filter(ep => ep.type === 2).length,
        ending_episodes: episodes.filter(ep => ep.type === 3).length,
        pv_episodes: episodes.filter(ep => ep.type === 4).length,
        other_episodes: episodes.filter(ep => ep.type === 6).length
      }
      
      // 设置核心数据
      episodeStats.value = calculatedStats
      bangumiEpisodes.value = episodes
      
      // 尝试获取资源可用性数据（可选，失败时优雅降级）
      try {
        const availabilityData = await BangumiApiService.getEpisodeAvailability(props.bangumiId)
        episodeAvailability.value = availabilityData
      } catch (availabilityErr) {
        console.warn('资源可用性获取失败，将显示为暂无资源:', availabilityErr)
        // 设置为null，子组件会优雅处理（显示所有章节为"暂无资源"）
        episodeAvailability.value = null
      }
      
    } catch (err) {
      console.error('获取Bangumi章节信息失败:', err)
      error.value = '获取章节信息失败，请稍后重试'
    } finally {
      loading.value = false
    }
  }
  
  // 组件挂载时获取数据
  onMounted(() => {
    fetchBangumiEpisodes()
  })
  </script>
  
  <style scoped>
  .episode-display {
    /* 容器样式，让子组件决定具体样式 */
  }
  
  .loading-state, .error-state {
    text-align: center;
    padding: 2rem;
    color: #6c757d;
  }
  
  .error-state {
    color: #dc3545;
  }
  

  </style>