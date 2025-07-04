// =============================================================================
// Scheduler API Service
// =============================================================================

import { apiClient } from '../common/common';
import type { ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobResponse } from './schedulerTypes';

export class ScheduledJobApiService {
    /**
     * 获取所有计划任务列表
     */
    static async listScheduledJobs(): Promise<ScheduledJobResponse[]> {
        return await apiClient.get('/scheduler/jobs');
    }

    /**
     * 创建新的计划任务
     * @param data 计划任务创建数据
     */
    static async createScheduledJob(data: ScheduledJobCreate):
        Promise<ScheduledJobResponse> {
        return await apiClient.post('/scheduler/jobs', data);
    }

    /**
     * 更新特定计划任务
     * @param job_id 计划任务的job_id
     * @param data 计划任务更新数据
     */
    static async updateScheduledJob(job_id: string, data: ScheduledJobUpdate):
        Promise<ScheduledJobResponse> {
        return await apiClient.put(`/scheduler/jobs/${job_id}`, data);
    }

    /**
     * 删除特定计划任务
     * @param job_id 计划任务的job_id
     */
    static async deleteScheduledJob(job_id: string):
        Promise<ScheduledJobResponse> {
        return await apiClient.delete(`/scheduler/jobs/${job_id}`);
    }

    /**
     * 切换特定计划任务的启用/禁用状态
     * @param job_id 计划任务的job_id
     */
    static async toggleScheduledJob(job_id: string):
        Promise<ScheduledJobResponse> {
        return await apiClient.post(`/scheduler/jobs/${job_id}/toggle`);
    }
}

export default ScheduledJobApiService;
