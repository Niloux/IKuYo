/**
 * 订阅状态管理Store
 * 管理用户订阅数据，提供乐观更新和缓存功能
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import subscriptionApiService from '../services/subscription/subscriptionApiService'
import bangumiApiService from '../services/bangumi/bangumiApiService'
import { useFeedbackStore } from './feedbackStore'
import type {
    SubscriptionWithAnime,
    GetSubscriptionsParams,
    PaginationInfo,
    UserSubscription
} from '../services/subscription/subscriptionTypes'
import type { BangumiCalendarItem } from '../services/bangumi/bangumiTypes'

export const useSubscriptionStore = defineStore('subscription', () => {
    // 状态
    const subscriptions = ref<SubscriptionWithAnime[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)
    const pagination = ref<PaginationInfo>({
        page: 1,
        limit: 20,
        total: 0,
        pages: 0
    })

    // 当前查询参数
    const currentParams = ref<GetSubscriptionsParams>({
        sort: 'subscribed_at',
        order: 'desc',
        page: 1,
        limit: 20
    })

    const feedbackStore = useFeedbackStore()

    /**
     * 计算属性：订阅的番剧ID集合，用于快速查询订阅状态
     */
    const subscribedBangumiIds = computed(() => {
        return new Set(subscriptions.value.map(sub => sub.bangumi_id))
    })

    /**
     * 检查是否已订阅指定番剧
     */
    const isSubscribed = (bangumiId: number): boolean => {
        return subscribedBangumiIds.value.has(bangumiId)
    }

    /**
     * 获取订阅列表（包含番剧详情）
     */
    const fetchSubscriptions = async (params: GetSubscriptionsParams = {}) => {
        try {
            loading.value = true
            error.value = null

            // 合并参数
            const finalParams = { ...currentParams.value, ...params }
            currentParams.value = finalParams

            // 获取订阅列表
            const response = await subscriptionApiService.getSubscriptions(finalParams)

            // 批量获取番剧详情
            const animeDetails = await Promise.all(
                response.subscriptions.map(sub =>
                    bangumiApiService.getSubject(sub.bangumi_id).catch(() => null)
                )
            )

            // 组合数据
            const subscriptionsWithAnime: SubscriptionWithAnime[] = response.subscriptions
                .map((sub, index) => {
                    const anime = animeDetails[index]
                    if (!anime) return null
                    return {
                        ...sub,
                        anime: anime as unknown as BangumiCalendarItem  // 类型断言
                    }
                })
                .filter(Boolean) as SubscriptionWithAnime[]

            subscriptions.value = subscriptionsWithAnime
            pagination.value = response.pagination

        } catch (err) {
            error.value = err instanceof Error ? err.message : '获取订阅列表失败'
            feedbackStore.showError(error.value)
        } finally {
            loading.value = false
        }
    }

    /**
     * 乐观订阅：立即更新UI，然后调用API
     */
    const optimisticSubscribe = async (anime: BangumiCalendarItem) => {
        // 立即添加到列表（乐观更新）
        const optimisticSubscription: SubscriptionWithAnime = {
            user_id: '',
            bangumi_id: anime.id,
            subscribed_at: Date.now() / 1000,
            anime,
            anime_name: anime.name,
            anime_name_cn: anime.name_cn,
            anime_rating: anime.rating?.score,
            anime_air_date: anime.air_date,
            anime_air_weekday: anime.air_weekday
        }

        subscriptions.value.unshift(optimisticSubscription)

        try {
            // 调用API确认订阅
            await subscriptionApiService.subscribe(anime.id)
            feedbackStore.showToast('订阅成功', 'success')
        } catch (err) {
            // 如果失败，移除乐观添加的项目
            subscriptions.value = subscriptions.value.filter(sub => sub.bangumi_id !== anime.id)
            const errorMsg = err instanceof Error ? err.message : '订阅失败'
            feedbackStore.showError(errorMsg)
            throw err
        }
    }

    /**
     * 乐观取消订阅：立即更新UI，然后调用API
     */
    const optimisticUnsubscribe = async (bangumiId: number) => {
        // 保存原始数据以便回滚
        const originalSubscriptions = [...subscriptions.value]

        // 立即从列表中移除（乐观更新）
        subscriptions.value = subscriptions.value.filter(sub => sub.bangumi_id !== bangumiId)

        try {
            // 调用API确认取消订阅
            await subscriptionApiService.unsubscribe(bangumiId)
            feedbackStore.showToast('取消订阅成功', 'success')
        } catch (err) {
            // 如果失败，恢复原始数据
            subscriptions.value = originalSubscriptions
            const errorMsg = err instanceof Error ? err.message : '取消订阅失败'
            feedbackStore.showError(errorMsg)
            throw err
        }
    }

    /**
     * 标准订阅（等待API响应）
     */
    const subscribe = async (bangumiId: number) => {
        try {
            await subscriptionApiService.subscribe(bangumiId)
            feedbackStore.showToast('订阅成功', 'success')
            // 重新获取列表以确保数据一致性
            await fetchSubscriptions()
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : '订阅失败'
            feedbackStore.showError(errorMsg)
            throw err
        }
    }

    /**
     * 标准取消订阅（等待API响应）
     */
    const unsubscribe = async (bangumiId: number) => {
        try {
            await subscriptionApiService.unsubscribe(bangumiId)
            feedbackStore.showToast('取消订阅成功', 'success')
            // 重新获取列表以确保数据一致性
            await fetchSubscriptions()
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : '取消订阅失败'
            feedbackStore.showError(errorMsg)
            throw err
        }
    }

    /**
     * 切换订阅状态
     */
    const toggleSubscription = async (anime: BangumiCalendarItem) => {
        if (isSubscribed(anime.id)) {
            await optimisticUnsubscribe(anime.id)
        } else {
            await optimisticSubscribe(anime)
        }
    }

    /**
     * 搜索订阅
     */
    const searchSubscriptions = async (query: string) => {
        await fetchSubscriptions({ ...currentParams.value, search: query, page: 1 })
    }

    /**
     * 切换排序
     */
    const sortSubscriptions = async (sort: GetSubscriptionsParams['sort'], order: GetSubscriptionsParams['order'] = 'desc') => {
        await fetchSubscriptions({ ...currentParams.value, sort, order, page: 1 })
    }

    /**
     * 翻页
     */
    const goToPage = async (page: number) => {
        await fetchSubscriptions({ ...currentParams.value, page })
    }

    /**
     * 清空状态
     */
    const clear = () => {
        subscriptions.value = []
        error.value = null
        loading.value = false
        pagination.value = {
            page: 1,
            limit: 20,
            total: 0,
            pages: 0
        }
        currentParams.value = {
            sort: 'subscribed_at',
            order: 'desc',
            page: 1,
            limit: 20
        }
    }

    return {
        // 状态
        subscriptions,
        loading,
        error,
        pagination,
        currentParams,

        // 计算属性
        subscribedBangumiIds,

        // 方法
        isSubscribed,
        fetchSubscriptions,
        optimisticSubscribe,
        optimisticUnsubscribe,
        subscribe,
        unsubscribe,
        toggleSubscription,
        searchSubscriptions,
        sortSubscriptions,
        goToPage,
        clear
    }
})
