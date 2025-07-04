/**
 * 订阅功能相关类型定义
 */

import type { BangumiCalendarItem } from '../bangumi/bangumiTypes'

// 基础订阅记录
export interface UserSubscription {
    id?: number
    user_id: string
    bangumi_id: number
    subscribed_at: number
    notes?: string
    // 缓存的番剧数据
    anime_name?: string
    anime_name_cn?: string
    anime_rating?: number
    anime_air_date?: string
    anime_air_weekday?: number
}

// 包含完整番剧信息的订阅记录
export interface SubscriptionWithAnime extends UserSubscription {
    anime: BangumiCalendarItem
}

// 订阅状态检查响应
export interface SubscriptionStatus {
    subscribed: boolean
    subscribed_at?: number
    notes?: string
}

// 获取订阅列表的请求参数
export interface GetSubscriptionsParams {
    sort?: 'subscribed_at' | 'rating' | 'air_date' | 'name'
    order?: 'asc' | 'desc'
    search?: string
    page?: number
    limit?: number
}

// 分页信息
export interface PaginationInfo {
    page: number
    limit: number
    total: number
    pages: number
}

// 获取订阅列表的响应
export interface SubscriptionsResponse {
    subscriptions: UserSubscription[]
    pagination: PaginationInfo
}

// 订阅列表的完整响应（包含番剧详情）
export interface SubscriptionsWithAnimeResponse {
    subscriptions: SubscriptionWithAnime[]
    pagination: PaginationInfo
}

// API错误响应
export interface SubscriptionError {
    message: string
    code?: string
}

// 订阅操作的结果
export interface SubscriptionResult {
    success: boolean
    error?: SubscriptionError
    data?: any
}
