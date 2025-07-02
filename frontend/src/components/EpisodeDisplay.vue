<template>
    <div class="episode-display">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <p>{{ loadingProgress || '正在加载章节信息...' }}</p>
        <div v-if="batchProgress" class="batch-progress">
          <p>进度：{{ batchProgress.current }} / {{ batchProgress.total }}</p>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: (batchProgress.current / batchProgress.total) * 100 + '%' }"
            ></div>
          </div>
        </div>
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
  import BangumiApiService, { type BangumiEpisode } from '@/services/api'

  // Props定义
  interface Props {
    bangumiId: number
  }

  const props = defineProps<Props>()

  // 本地统计信息接口定义
  interface EpisodeStats {
    total: number
    main_episodes: number
    special_episodes: number
    opening_episodes: number
    ending_episodes: number
    pv_episodes: number
    other_episodes: number
  }

  // 响应式数据
  const loading = ref(true)
  const error = ref<string | null>(null)
  const bangumiEpisodes = ref<BangumiEpisode[]>([])
  const episodeStats = ref<EpisodeStats | null>(null)
  const episodeAvailability = ref<any>(null)

  // 批量获取进度状态
  const loadingProgress = ref<string>('')
  const batchProgress = ref<{ current: number; total: number } | null>(null)

  // 智能显示模式判断
  const MODERN_ANIME_THRESHOLD = 26

  const displayMode = computed(() => {
    if (!episodeStats.value) return 'carousel'
    return episodeStats.value.main_episodes <= MODERN_ANIME_THRESHOLD ? 'carousel' : 'grid'
  })

  // 分页获取完整章节数据
  const fetchAllEpisodes = async (): Promise<BangumiEpisode[]> => {
    const allEpisodes: BangumiEpisode[] = []
    let offset = 0
    const limit = 1000
    let totalCount = 0

    while (true) {
      const batchData = await BangumiApiService.getBangumiEpisodes(props.bangumiId, 0, limit, offset)

      // 首次获取时初始化进度信息
      if (offset === 0) {
        totalCount = batchData.total
        const totalBatches = Math.ceil(totalCount / limit)
        batchProgress.value = { current: 1, total: totalBatches }

        if (totalBatches > 1) {
          loadingProgress.value = `章节较多，需分 ${totalBatches} 批获取 (总计 ${totalCount} 集)`
        }
      } else {
        const currentBatch = Math.floor(offset / limit) + 1
        batchProgress.value = {
          current: currentBatch,
          total: batchProgress.value?.total || 1
        }
        loadingProgress.value = `正在获取第 ${currentBatch} 批章节数据...`
      }

      allEpisodes.push(...batchData.data)

      // 检查是否获取完毕
      if (batchData.data.length < limit || allEpisodes.length >= totalCount) {
        break
      }

      offset += limit
    }

    return allEpisodes
  }

  // 主数据获取函数
  const fetchBangumiEpisodes = async () => {
    try {
      loading.value = true
      error.value = null
      loadingProgress.value = '正在获取章节信息...'
      batchProgress.value = null

      // 获取所有章节数据
      const episodes = await fetchAllEpisodes()

      // 计算统计信息
      episodeStats.value = {
        total: episodes.length,
        main_episodes: episodes.filter(ep => ep.type === 0).length,
        special_episodes: episodes.filter(ep => ep.type === 1).length,
        opening_episodes: episodes.filter(ep => ep.type === 2).length,
        ending_episodes: episodes.filter(ep => ep.type === 3).length,
        pv_episodes: episodes.filter(ep => ep.type === 4).length,
        other_episodes: episodes.filter(ep => ep.type === 6).length
      }

      bangumiEpisodes.value = episodes
      loadingProgress.value = '正在获取资源可用性数据...'

      // 获取资源可用性数据（可选）
      try {
        const availabilityData = await BangumiApiService.getEpisodeAvailability(props.bangumiId)
        episodeAvailability.value = availabilityData
      } catch (availabilityErr) {
        console.warn('资源可用性获取失败，将显示为暂无资源:', availabilityErr)
        episodeAvailability.value = null
      }

    } catch (err) {
      console.error('获取Bangumi章节信息失败:', err)
      error.value = '获取章节信息失败，请稍后重试'
    } finally {
      loading.value = false
      loadingProgress.value = ''
      batchProgress.value = null
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

  .batch-progress {
    margin-top: 1rem;
  }

  .progress-bar {
    width: 200px;
    height: 6px;
    background-color: #e9ecef;
    border-radius: 3px;
    margin: 0.5rem auto;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background-color: #3498db;
    transition: width 0.3s ease;
  }

  </style>
