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
        :episode-stats="episodeStats"
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
  

  
  // 获取Bangumi章节数据（并行优化）
  const fetchBangumiEpisodes = async () => {
    try {
      loading.value = true
      error.value = null
      
      console.log(`🚀 开始并行获取Bangumi章节信息 (subject_id: ${props.bangumiId})`)
      const startTime = performance.now()
      
      // 智能获取章节信息：先获取少量数据判断总数，再决定是否需要更多
      const [initialEpisodesData, availabilityData] = await Promise.all([
        BangumiApiService.getBangumiEpisodes(
          props.bangumiId,
          0, // 只获取正片
          50 // 先获取前50集，足够判断大部分动画
        ),
        BangumiApiService.getEpisodeAvailability(props.bangumiId)
      ])
      
      let episodesData = initialEpisodesData
      
      // 如果是长篇动画且还有更多集数，继续获取
      if (initialEpisodesData.total > 50) {
        console.log(`📺 检测到长篇动画，总集数: ${initialEpisodesData.total}，继续获取剩余集数...`)
        const remainingEpisodesData = await BangumiApiService.getBangumiEpisodes(
          props.bangumiId,
          0,
          Math.min(initialEpisodesData.total, 500) // 最多获取500集，防止过度请求
        )
        episodesData = remainingEpisodesData
      }
      
      // 在前端计算统计信息，避免重复API调用
      const episodes = episodesData.data
      const stats = {
        total: episodes.length,
        main_episodes: episodes.filter(ep => ep.type === 0).length,
        special_episodes: episodes.filter(ep => ep.type === 1).length, 
        opening_episodes: episodes.filter(ep => ep.type === 2).length,
        ending_episodes: episodes.filter(ep => ep.type === 3).length,
        pv_episodes: episodes.filter(ep => ep.type === 4).length,
        other_episodes: episodes.filter(ep => ep.type === 6).length
      }
      
      episodeStats.value = stats
      bangumiEpisodes.value = episodes
      episodeAvailability.value = availabilityData
      
      const loadTime = performance.now() - startTime
      console.log(`✅ 并行获取章节信息完成: 正片${stats.main_episodes}集，耗时: ${loadTime.toFixed(2)}ms`)
      
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