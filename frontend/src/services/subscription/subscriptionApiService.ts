/**
 * 订阅API服务
 * 封装所有订阅相关的后端API调用
 */

import { UserManager } from '../../utils/userManager'
import type {
    UserSubscription,
    SubscriptionStatus,
    GetSubscriptionsParams,
    SubscriptionsResponse,
    SubscriptionResult
} from './subscriptionTypes'
import { apiClient } from '../common/common'

class SubscriptionApiService {
    private readonly baseURL = '/subscriptions'

    /**
     * 获取HTTP请求头，包含用户ID
     */
    private getHeaders(): HeadersInit {
        return {
            'Content-Type': 'application/json',
            'X-User-Id': UserManager.getUserId()
        }
    }

    /**
     * 处理API响应
     */
    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
        }
        return response.json()
    }

    /**
     * 添加订阅
     */
    async subscribe(bangumiId: number): Promise<UserSubscription> {
        return apiClient.post(`${this.baseURL}/${bangumiId}`)
    }

    /**
     * 取消订阅
     */
    async unsubscribe(bangumiId: number): Promise<void> {
        await apiClient.delete(`${this.baseURL}/${bangumiId}`)
    }

    /**
     * 获取订阅列表
     */
    async getSubscriptions(params: GetSubscriptionsParams = {}): Promise<SubscriptionsResponse> {
        const searchParams = new URLSearchParams()
        if (params.sort) searchParams.set('sort', params.sort)
        if (params.order) searchParams.set('order', params.order)
        if (params.search) searchParams.set('search', params.search)
        if (params.page) searchParams.set('page', params.page.toString())
        if (params.limit) searchParams.set('limit', params.limit.toString())
        const url = `${this.baseURL}?${searchParams.toString()}`
        return apiClient.get(url)
    }

    /**
     * 检查订阅状态
     */
    async checkSubscription(bangumiId: number): Promise<SubscriptionStatus> {
        return apiClient.get(`${this.baseURL}/${bangumiId}`)
    }

    /**
     * 安全的订阅操作（带错误处理）
     */
    async safeSubscribe(bangumiId: number): Promise<SubscriptionResult> {
        try {
            const data = await this.subscribe(bangumiId)
            return { success: true, data }
        } catch (error) {
            return {
                success: false,
                error: {
                    message: error instanceof Error ? error.message : '订阅失败'
                }
            }
        }
    }

    /**
     * 安全的取消订阅操作（带错误处理）
     */
    async safeUnsubscribe(bangumiId: number): Promise<SubscriptionResult> {
        try {
            await this.unsubscribe(bangumiId)
            return { success: true }
        } catch (error) {
            return {
                success: false,
                error: {
                    message: error instanceof Error ? error.message : '取消订阅失败'
                }
            }
        }
    }
}

// 导出单例实例
export default new SubscriptionApiService()
