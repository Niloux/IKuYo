import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { EpisodeResourcesData } from '../services/bangumi/bangumiTypes'

interface ResourceQuery {
    bangumiId: number
    episodeNumber?: number
    resolution?: string
    subtitleType?: string
    limit?: number
    offset?: number
}

export const useResourceStore = defineStore('resourceStore', () => {
    // 缓存结构：key为bangumiId+episodeNumber+筛选+分页，value为资源数据
    const resourceCache = ref<Record<string, EpisodeResourcesData | null>>({})
    const loadingCache = ref<Record<string, boolean>>({})
    const errorCache = ref<Record<string, string | null>>({})

    // 当前查询参数
    const currentQuery = ref<ResourceQuery | null>(null)

    // 获取当前key
    const getQueryKey = (query: ResourceQuery) => {
        // 兼容全量和单集资源缓存
        const parts = [
            query.bangumiId,
            query.episodeNumber !== undefined ? `ep${query.episodeNumber}` : 'all',
            query.resolution || '',
            query.subtitleType || '',
            query.limit ?? '',
            query.offset ?? ''
        ]
        return parts.join('-')
    }
    const currentKey = computed(() => currentQuery.value ? getQueryKey(currentQuery.value) : '')

    // 当前数据
    const resourcesData = computed(() => resourceCache.value[currentKey.value] || null)
    const loading = computed(() => loadingCache.value[currentKey.value] || false)
    const error = computed(() => errorCache.value[currentKey.value] || null)

    /**
     * 拉取资源列表：自动根据是否有episodeNumber选择API
     */
    async function fetchResources(query: ResourceQuery) {
        const key = getQueryKey(query)
        currentQuery.value = query
        loadingCache.value[key] = true
        errorCache.value[key] = null
        try {
            let data: EpisodeResourcesData | null
            if (query.episodeNumber !== undefined) {
                // 按集拉取
                data = await BangumiApiService.getEpisodeResources(query.bangumiId, query.episodeNumber)
                if (data === null) {
                    // 404视为无资源，正常情况
                    resourceCache.value[key] = null
                    return
                }
            } else {
                // 全量拉取
                data = await BangumiApiService.getAnimeResources(query.bangumiId, {
                    resolution: query.resolution,
                    subtitle_type: query.subtitleType,
                    limit: query.limit,
                    offset: query.offset
                })
            }
            resourceCache.value[key] = data
        } catch (err: any) {
            errorCache.value[key] = err?.message || '加载资源列表失败'
            resourceCache.value[key] = null
        } finally {
            loadingCache.value[key] = false
        }
    }

    // 刷新当前资源
    async function refreshResources() {
        if (currentQuery.value) {
            await fetchResources(currentQuery.value)
        }
    }

    // 清理缓存
    function clear() {
        resourceCache.value = {}
        loadingCache.value = {}
        errorCache.value = {}
        currentQuery.value = null
    }

    return {
        resourcesData,
        loading,
        error,
        fetchResources,
        refreshResources,
        clear,
        currentQuery
    }
})
