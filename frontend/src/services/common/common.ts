// =============================================================================
// Common Types
// =============================================================================

import axios, { type AxiosResponse } from 'axios'
import { useFeedbackStore } from '../../stores/feedbackStore';

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

// 请求拦截器 - 自动开启loading
apiClient.interceptors.request.use(
    (config) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.showLoading();
        return config;
    },
    (error) => {
        const feedbackStore = useFeedbackStore();
        feedbackStore.hideLoading();
        return Promise.reject(error);
    }
);

// 响应拦截器 - 统一处理响应数据和异常，自动关闭loading和推送错误
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
        if (response && response.status === 404 && config && config.url) {
            const url = config.url;
            // 匹配/animes/{id}/episodes/availability 或 /animes/{id}/resources?episode=
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

export { apiClient }
