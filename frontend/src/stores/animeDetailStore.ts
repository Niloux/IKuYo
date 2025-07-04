import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { BangumiSubject, BangumiEpisode } from '../services/bangumi/bangumiTypes'
import { useAsyncAction } from './asyncUtils'

/**
 * Pinia 番剧详情 Store
 * 管理番剧详情、集数、可用性等状态和异步操作
 */
export const useAnimeDetailStore = defineStore('animeDetail', () => {
    const bangumiId = ref<number | null>(null)
    const subject = ref<BangumiSubject | null>(null)
    const episodes = ref<BangumiEpisode[]>([])
    const availability = ref<any>(null)

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
    }

    /**
     * 并发请求所有详情数据
     * @param id 番剧ID
     * @returns Promise<{ subject, episodes, availability }>
     */
    const fetchAllAsync = useAsyncAction(async (id: number) => {
        if (bangumiId.value === id && subject.value && episodes.value.length > 0 && availability.value) {
            // 已有数据且id未变，直接复用
            return { subject: subject.value, episodes: episodes.value, availability: availability.value }
        }
        clear()
        bangumiId.value = id
        // 分别请求主数据和资源可用性
        const [subjectRes, episodesRes] = await Promise.all([
            BangumiApiService.getSubject(id),
            BangumiApiService.getBangumiEpisodes(id, 0, 1000, 0)
        ])
        subject.value = subjectRes
        episodes.value = episodesRes.data
        // availability单独catch
        try {
            const avail = await BangumiApiService.getEpisodeAvailability(id)
            availability.value = avail // null视为无资源
        } catch (err: any) {
            availability.value = null
            // 404静默，其他异常交由UI层处理
            if (!err?.response || err?.response?.status !== 404) {
                throw new Error('资源可用性加载失败')
            }
        }
        return { subject: subject.value, episodes: episodes.value, availability: availability.value }
    })
    const fetchAll = async (id: number) => {
        return await fetchAllAsync.run(id)
    }

    /**
     * 单独请求番剧详情
     * @param id 番剧ID
     * @returns Promise<BangumiSubject>
     */
    const fetchSubjectAsync = useAsyncAction(async (id: number) => {
        const res = await BangumiApiService.getSubject(id)
        subject.value = res
        return res
    })
    const fetchSubject = async (id: number) => {
        return await fetchSubjectAsync.run(id)
    }

    const fetchEpisodesAsync = useAsyncAction(async (id: number) => {
        const res = await BangumiApiService.getBangumiEpisodes(id, 0, 1000, 0)
        episodes.value = res.data
        return res.data
    })
    const fetchEpisodes = async (id: number) => {
        return await fetchEpisodesAsync.run(id)
    }

    const fetchAvailabilityAsync = useAsyncAction(async (id: number) => {
        try {
            const avail = await BangumiApiService.getEpisodeAvailability(id)
            availability.value = avail
            return avail
        } catch (err: any) {
            availability.value = null
            if (!err?.response || err?.response?.status !== 404) {
                throw new Error('加载资源可用性失败')
            }
            return null
        }
    })
    const fetchAvailability = async (id: number) => {
        return await fetchAvailabilityAsync.run(id)
    }

    return {
        bangumiId,
        subject,
        episodes,
        availability,
        mainEpisodes,
        hasResource,
        fetchAll,
        fetchSubject,
        fetchEpisodes,
        fetchAvailability,
        clear,
        fetchAllAsync,
        fetchSubjectAsync,
        fetchEpisodesAsync,
        fetchAvailabilityAsync
    }
})
