// =============================================================================
// Common Types
// =============================================================================

import axios, { type AxiosResponse } from 'axios'

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

// 全局通知（Toast）工具函数（假设已在全局注册，或可替换为你项目的通知实现）
function showToast(message: string, type: 'error' | 'info' | 'success' = 'error') {
    // 这里假设有全局window.$toast，实际可替换为Element Plus/Antd等通知API
    if (window && (window as any).$toast) {
        (window as any).$toast[type](message)
    } else {
        // 兜底：用alert
        alert(message)
    }
}

// 响应拦截器 - 统一处理响应数据
apiClient.interceptors.response.use(
    (response: AxiosResponse) => {// 直接返回data部分
        return response.data
    },
    (error) => {
        const { response } = error
        if (response) {
            const status = response.status
            let msg = response.data?.message || '请求发生错误'
            switch (status) {
                case 401:
                case 403:
                    msg = '认证失败，请重新登录'
                    showToast(msg, 'error')
                    window.location.href = '/login'
                    break;
                case 404:
                    msg = '资源未找到'
                    showToast(msg, 'error')
                    break;
                case 500:
                    msg = '服务器内部错误'
                    showToast(msg, 'error')
                    break;
                default:
                    showToast(msg, 'error')
                    break
            }
        }
        else {
            showToast('网络连接失败', 'error')
        }
        return Promise.reject(error)
    })

export { apiClient }
