import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { EpisodeResourcesData } from '../services/bangumi/bangumiTypes'

interface ResourceQuery {
    bangumiId: number
    resolution?: string
    subtitleType?: string
    limit?: number
    offset?: number
}

function getQueryKey(query: ResourceQuery) {
    return [
        query.bangumiId,
        query.resolution || '',
        query.subtitleType || '',
        query.limit || 100,
        query.offset || 0
    ].join('-')
}

export const useResourceStore = defineStore('resourceStore', () => {
    // 缓存结构：key为bangumiId+筛选+分页，value为资源数据
    const resourceCache = ref<Record<string, EpisodeResourcesData | null>>({})
    const loadingCache = ref<Record<string, boolean>>({})
    const errorCache = ref<Record<string, string | null>>({})

    // 当前查询参数
    const currentQuery = ref<ResourceQuery | null>(null)

    // 获取当前key
    const currentKey = computed(() => currentQuery.value ? getQueryKey(currentQuery.value) : '')

    // 当前数据
    const resourcesData = computed(() => resourceCache.value[currentKey.value] || null)
    const loading = computed(() => loadingCache.value[currentKey.value] || false)
    const error = computed(() => errorCache.value[currentKey.value] || null)

    // 拉取资源列表
    async function fetchResources(query: ResourceQuery) {
        const key = getQueryKey(query)
        currentQuery.value = query
        loadingCache.value[key] = true
        errorCache.value[key] = null
        try {
            const data = await BangumiApiService.getAnimeResources(query.bangumiId, {
                resolution: query.resolution,
                subtitle_type: query.subtitleType,
                limit: query.limit,
                offset: query.offset
            })
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
