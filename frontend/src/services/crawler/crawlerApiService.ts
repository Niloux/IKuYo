// =============================================================================
// Crawler API Service
// =============================================================================

import { apiClient } from '../common/common';
import type { CrawlerTaskCreate, TaskResponse } from './crawlerTypes';

export class CrawlerApiService {
    /**
     * 创建新的爬虫任务
     * @param data 任务创建数据
     */
    static async createTask(data: CrawlerTaskCreate): Promise<TaskResponse> {
        return await apiClient.post('/crawler/tasks', data)
    }

    /**
     * 获取所有爬虫任务列表
     * @param page 页码，从1开始
     * @param pageSize 每页数量
     */
    static async listTasks(page: number = 1, pageSize: number = 10):
        Promise<TaskResponse[]> {
        return await apiClient.get(
            '/crawler/tasks', { params: { page, page_size: pageSize } })
    }

    /**
     * 获取特定爬虫任务的详情
     * @param taskId 任务ID
     */
    static async getTask(taskId: number): Promise<TaskResponse> {
        return await apiClient.get(`/crawler/tasks/${taskId}`)
    }

    /**
     * 取消特定爬虫任务
     * @param taskId 任务ID
     */
    static async cancelTask(taskId: number): Promise<TaskResponse> {
        return await apiClient.delete(`/crawler/tasks/${taskId}`)
    }

    /**
     * 获取特定爬虫任务的进度 (HTTP轮询方式，不推荐用于实时更新)
     * @param taskId 任务ID
     */
    static async getTaskProgress(taskId: number): Promise<any> {
        return await apiClient.get(`/crawler/tasks/${taskId}/progress`)
    }

    /**
     * 连接到特定爬虫任务的WebSocket进度更新
     * @param taskId 任务ID
     * @returns WebSocket实例
     */
    static connectTaskProgressWs(taskId: number): WebSocket {
        // 优先使用VITE_WS_BASE_URL环境变量
        const wsBase = import.meta.env.VITE_WS_BASE_URL;
        let wsUrl: string;
        if (wsBase && wsBase.trim() !== '') {
            // 确保结尾无斜杠
            const base = wsBase.replace(/\/$/, '');
            wsUrl = `${base}/crawler/tasks/${taskId}/ws`;
        } else {
            // 回退到当前host
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl = `${wsProtocol}//${window.location.host}/crawler/tasks/${taskId}/ws`;
        }
        return new WebSocket(wsUrl);
    }
}

export default CrawlerApiService;
