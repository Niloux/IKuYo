import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { BangumiSubject, BangumiEpisode } from '../services/bangumi/bangumiTypes'

export const useAnimeDetailStore = defineStore('animeDetail', () => {
    const bangumiId = ref<number | null>(null)
    const subject = ref<BangumiSubject | null>(null)
    const episodes = ref<BangumiEpisode[]>([])
    const availability = ref<any>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

    // 获取主集数
    const mainEpisodes = computed(() => episodes.value.filter(ep => ep.type === 0))
    // 是否有可用资源
    const hasResource = computed(() => {
        if (!availability.value || !availability.value.episodes) return false
        return Object.values(availability.value.episodes).some((ep: any) => ep.available)
    })

    // 清空所有state
    function clear() {
        bangumiId.value = null
        subject.value = null
        episodes.value = []
        availability.value = null
        loading.value = false
        error.value = null
    }

    // 并发请求所有详情数据
    async function fetchAll(id: number) {
        if (bangumiId.value === id && subject.value && episodes.value.length > 0 && availability.value) {
            // 已有数据且id未变，直接复用
            return
        }
        clear()
        bangumiId.value = id
        loading.value = true
        error.value = null
        try {
            // 分别请求主数据和资源可用性
            const [subjectRes, episodesRes] = await Promise.all([
                BangumiApiService.getSubject(id),
                BangumiApiService.getBangumiEpisodes(id, 0, 1000, 0)
            ])
            subject.value = subjectRes
            episodes.value = episodesRes.data
            // availability单独catch
            try {
                availability.value = await BangumiApiService.getEpisodeAvailability(id)
            } catch (err: any) {
                // 仅404时静默，其他错误toast
                if (err?.response?.status === 404) {
                    availability.value = null
                } else {
                    availability.value = null
                    if (window && window.$toast) window.$toast.error('资源可用性加载失败')
                }
            }
        } catch (err: any) {
            error.value = err?.message || '加载番剧详情失败'
            if (window && window.$toast) window.$toast.error(String(error.value))
        } finally {
            loading.value = false
        }
    }

    // 单独请求
    async function fetchSubject(id: number) {
        try {
            subject.value = await BangumiApiService.getSubject(id)
        } catch (err: any) {
            error.value = err?.message || '加载番剧详情失败'
            if (window && window.$toast) window.$toast.error(String(error.value))
        }
    }
    async function fetchEpisodes(id: number) {
        try {
            const res = await BangumiApiService.getBangumiEpisodes(id, 0, 1000, 0)
            episodes.value = res.data
        } catch (err: any) {
            error.value = err?.message || '加载集数失败'
            if (window && window.$toast) window.$toast.error(String(error.value))
        }
    }
    async function fetchAvailability(id: number) {
        try {
            availability.value = await BangumiApiService.getEpisodeAvailability(id)
        } catch (err: any) {
            error.value = err?.message || '加载资源可用性失败'
            if (window && window.$toast) window.$toast.error(String(error.value))
        }
    }

    return {
        bangumiId,
        subject,
        episodes,
        availability,
        loading,
        error,
        mainEpisodes,
        hasResource,
        fetchAll,
        fetchSubject,
        fetchEpisodes,
        fetchAvailability,
        clear
    }
})
