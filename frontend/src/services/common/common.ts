// =============================================================================
// Common Types
// =============================================================================

import axios, { type AxiosResponse } from 'axios'
import { useFeedbackStore } from '../../stores/feedbackStore';
import { debounce, throttle } from '../../utils/debounce'
import { UserManager } from '../../utils/userManager'

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// 创建axios实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 通用API响应类型
export interface ApiResponse<T = unknown> {
    success: boolean;
    message: string;
    data: T;
    total?: number;
}

// 请求拦截器 - 自动开启loading，并注入X-User-Id
apiClient.interceptors.request.use(
    (config) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.showLoading();
        // 自动注入 X-User-Id
        config.headers = config.headers || {};
        config.headers['X-User-Id'] = UserManager.getUserId();
        return config;
    },
    (error) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.hideLoading();
        return Promise.reject(error);
    }
);

// ================= 全局axios响应拦截器 =================
// 统一处理所有API请求的loading、异常和全局反馈
// 404白名单静默逻辑：对/animes/{id}/episodes/availability 和 /animes/{id}/resources?episode= 的404响应不弹窗，仅业务层处理
// 其他异常依然全局弹窗
apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.hideLoading();
        return response.data;
    },
    (error) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.hideLoading();
        const { response, config } = error;
        let msg = '请求发生错误';
        // 404白名单静默处理
        // 命中/animes/{id}/episodes/availability 或 /animes/{id}/resources?episode= 的404响应时，不弹窗
        if (response && response.status === 404 && config && config.url) {
            const url = config.url;
            const isAvailability = /\/animes\/\d+\/episodes\/availability$/.test(url);
            const isEpisodeResource = /\/animes\/\d+\/resources\?episode=\d+/.test(url);
            if (isAvailability || isEpisodeResource) {
                // 白名单命中，静默处理，不弹窗
                return Promise.reject(error);
            }
        }
        if (response) {
            const status = response.status;
            msg = response.data?.message || msg;
            switch (status) {
                case 401:
                case 403:
                    msg = '认证失败，请重新登录';
                    feedbackStore.showError(msg);
                    window.location.href = '/login';
                    break;
                case 404:
                    msg = '资源未找到';
                    feedbackStore.showError(msg);
                    break;
                case 500:
                    msg = '服务器内部错误';
                    feedbackStore.showError(msg);
                    break;
                default:
                    feedbackStore.showError(msg);
                    break;
            }
        } else {
            feedbackStore.showError('网络连接失败');
        }
        return Promise.reject(error);
    }
);

/**
 * 全局API防抖工具
 * @param fn 需要防抖的API函数
 * @param delay 防抖间隔
 */
export function debounceRequest<T extends (...args: any[]) => Promise<any>>(fn: T, delay = 300) {
    return debounce(fn, delay)
}

/**
 * 全局API节流工具
 * @param fn 需要节流的API函数
 * @param delay 节流间隔
 */
export function throttleRequest<T extends (...args: any[]) => Promise<any>>(fn: T, delay = 500) {
    return throttle(fn, delay)
}

/**
 * 异步防抖工具（返回Promise，适用于异步API）
 */
export function debounceAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    delay = 300
): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
    let timeoutId: number | null = null
    let lastReject: ((reason?: any) => void) | null = null
    return (...args: Parameters<T>) => {
        if (timeoutId) {
            clearTimeout(timeoutId)
            if (lastReject) lastReject('debounced')
        }
        return new Promise<Awaited<ReturnType<T>>>((resolve, reject) => {
            lastReject = reject
            timeoutId = setTimeout(() => {
                fn(...args).then(resolve).catch(reject)
                timeoutId = null
                lastReject = null
            }, delay) as unknown as number
        })
    }
}

/**
 * 异步节流工具（返回Promise，适用于异步API）
 */
export function throttleAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    delay = 500
): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
    let lastCall = 0
    let pending: Promise<Awaited<ReturnType<T>>> | null = null
    return (...args: Parameters<T>) => {
        const now = Date.now()
        if (now - lastCall >= delay) {
            lastCall = now
            pending = fn(...args)
            return pending
        } else if (pending) {
            return pending
        } else {
            return new Promise<Awaited<ReturnType<T>>>((resolve) => {
                setTimeout(() => {
                    lastCall = Date.now()
                    pending = fn(...args)
                    pending.then(resolve)
                }, delay - (now - lastCall))
            })
        }
    }
}

export { apiClient }
