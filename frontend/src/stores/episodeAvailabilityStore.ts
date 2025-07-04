import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { EpisodeAvailabilityData } from '../services/bangumi/bangumiTypes'

export const useEpisodeAvailabilityStore = defineStore('episodeAvailabilityStore', () => {
    // 缓存结构：key为bangumiId，value为可用性数据
    const availabilityCache = ref<Record<number, EpisodeAvailabilityData | null>>({})
    const loadingCache = ref<Record<number, boolean>>({})
    const errorCache = ref<Record<number, string | null>>({})

    // 当前bangumiId
    const currentBangumiId = ref<number | null>(null)

    // 当前数据
    const availability = computed(() =>
        currentBangumiId.value !== null ? availabilityCache.value[currentBangumiId.value] || null : null
    )
    const loading = computed(() =>
        currentBangumiId.value !== null ? loadingCache.value[currentBangumiId.value] || false : false
    )
    const error = computed(() =>
        currentBangumiId.value !== null ? errorCache.value[currentBangumiId.value] || null : null
    )

    // 拉取可用性数据
    async function fetchAvailability(bangumiId: number) {
        currentBangumiId.value = bangumiId
        loadingCache.value[bangumiId] = true
        errorCache.value[bangumiId] = null
        try {
            const data = await BangumiApiService.getEpisodeAvailability(bangumiId)
            availabilityCache.value[bangumiId] = data
        } catch (err: any) {
            errorCache.value[bangumiId] = err?.message || '加载集数可用性失败'
            availabilityCache.value[bangumiId] = null
        } finally {
            loadingCache.value[bangumiId] = false
        }
    }

    // 刷新当前可用性
    async function refreshAvailability() {
        if (currentBangumiId.value !== null) {
            await fetchAvailability(currentBangumiId.value)
        }
    }

    // 清理缓存
    function clear() {
        availabilityCache.value = {}
        loadingCache.value = {}
        errorCache.value = {}
        currentBangumiId.value = null
    }

    return {
        availability,
        loading,
        error,
        fetchAvailability,
        refreshAvailability,
        clear,
        currentBangumiId
    }
})
