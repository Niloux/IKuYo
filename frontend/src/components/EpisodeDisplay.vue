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
      />
      
      <EpisodeGrid 
        v-else-if="displayMode === 'grid' && episodeStats"
        :bangumi-id="bangumiId"
        :total-episodes="episodeStats.main_episodes"
        :bangumi-episodes="bangumiEpisodes"
        :episode-stats="episodeStats"
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
  
  // 智能显示模式判断
  const MODERN_ANIME_THRESHOLD = 26
  
  const displayMode = computed(() => {
    if (!episodeStats.value) return 'carousel'
    return episodeStats.value.main_episodes <= MODERN_ANIME_THRESHOLD ? 'carousel' : 'grid'
  })
  

  
  // 获取Bangumi章节数据
  const fetchBangumiEpisodes = async () => {
    try {
      loading.value = true
      error.value = null
      
      console.log(`🔍 开始获取Bangumi章节信息 (subject_id: ${props.bangumiId})`)
      
      // 获取章节统计信息
      const stats = await BangumiApiService.getBangumiEpisodesStats(props.bangumiId)
      episodeStats.value = stats
      
      // 获取正片章节信息 (type: 0)
      const episodesData = await BangumiApiService.getBangumiEpisodes(
        props.bangumiId,
        0, // 只获取正片
        1000 // 足够大的数量
      )
      bangumiEpisodes.value = episodesData.data
      
      console.log(`✅ 成功获取章节信息: 正片${stats.main_episodes}集`)
      
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