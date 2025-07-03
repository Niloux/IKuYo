import {apiClient, type ApiResponse} from './api'

// =============================================================================
// TypeScript Interfaces for Backend Schemas
// Based on ikuyo/api/models/schemas.py
// =============================================================================

export interface CrawlerTaskCreate {
  mode: string
  year?: number
  season?: string
  start_url?: string
  limit?: number
}

export interface TaskResponse {
  id: number
  task_type: string
  status: string
  parameters?: string
  result_summary?: string
  created_at?: string // datetime objects are usually stringified in JSON
  started_at?: string
  completed_at?: string
  error_message?: string
  percentage?: number
  processed_items?: number
  total_items?: number
  processing_speed?: number
  estimated_remaining?: number
}

export interface ScheduledJobCreate {
  job_id: string
  name: string
  cron_expression: string
  parameters: any // This will be a JSON object, e.g., CrawlerTaskCreate
  enabled?: boolean
  description?: string
}

export interface ScheduledJobUpdate {
  name?: string
  cron_expression?: string
  parameters?: any
  enabled?: boolean
  description?: string
}

export interface ScheduledJobResponse {
  id?: number
  job_id: string
  name: string
  cron_expression: string
  parameters: any
  enabled: boolean
  description?: string
  created_at?: string
  updated_at?: string
}

// =============================================================================
// API Service for Crawler Tasks
// =============================================================================

export class CrawlerApiService {
  // --- Crawler Tasks ---

  /**
   * 创建新的爬虫任务
   * @param data 任务创建数据
   */
  static async createTask(data: CrawlerTaskCreate): Promise<TaskResponse> {
    const response: ApiResponse<TaskResponse> = await apiClient.post(
      '/crawler/tasks',
      data,
    )
    return response.data
  }

  /**
   * 获取所有爬虫任务列表
   * @param page 页码，从1开始
   * @param pageSize 每页数量
   */
  static async listTasks(page: number = 1, pageSize: number = 10):
      Promise<TaskResponse[]> {
    const response = await apiClient.get(
        '/crawler/tasks', {params: {page, page_size: pageSize}})
    return response as unknown as TaskResponse[]
  }

  /**
   * 获取特定爬虫任务的详情
   * @param taskId 任务ID
   */
  static async getTask(taskId: number): Promise<TaskResponse> {
    const response: ApiResponse<TaskResponse> = await apiClient.get(
      `/crawler/tasks/${taskId}`,
    )
    return response.data
  }

  /**
   * 取消特定爬虫任务
   * @param taskId 任务ID
   */
  static async cancelTask(taskId: number): Promise<TaskResponse> {
    const response: ApiResponse<TaskResponse> = await apiClient.delete(
      `/crawler/tasks/${taskId}`,
    )
    return response.data
  }

  /**
   * 获取特定爬虫任务的进度 (HTTP轮询方式，不推荐用于实时更新)
   * @param taskId 任务ID
   */
  static async getTaskProgress(taskId: number): Promise<any> {
    const response: ApiResponse<any> = await apiClient.get(
      `/crawler/tasks/${taskId}/progress`,
    )
    return response.data
  }

  /**
   * 连接到特定爬虫任务的WebSocket进度更新
   * @param taskId 任务ID
   * @returns WebSocket实例
   */
  static connectTaskProgressWs(taskId: number): WebSocket {
    // 注意：WebSocket连接需要使用ws://或wss://协议，并且通常与HTTP API使用不同的端口或路径
    // 这里的baseURL是HTTP的，需要根据实际WebSocket服务器地址调整
    // 假设WebSocket服务与HTTP服务在同一主机和端口，但路径不同
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = apiClient.defaults.baseURL?.replace(/https?:\/\//, '') // Remove http(s)://
    const wsUrl = `${wsProtocol}//${wsHost}/crawler/tasks/${taskId}/ws`
    return new WebSocket(wsUrl)
  }

  // --- Scheduled Jobs ---

  /**
   * 获取所有计划任务列表
   */
  static async listScheduledJobs(): Promise<ScheduledJobResponse[]> {
    const response: ApiResponse<ScheduledJobResponse[]> = await apiClient.get(
      '/api/v1/scheduler/jobs',
    )
    return response.data
  }

  /**
   * 创建新的计划任务
   * @param data 计划任务创建数据
   */
  static async createScheduledJob(
    data: ScheduledJobCreate,
  ): Promise<ScheduledJobResponse> {
    const response: ApiResponse<ScheduledJobResponse> = await apiClient.post(
      '/api/v1/scheduler/jobs',
      data,
    )
    return response.data
  }

  /**
   * 更新特定计划任务
   * @param job_id 计划任务的job_id
   * @param data 计划任务更新数据
   */
  static async updateScheduledJob(
    job_id: string,
    data: ScheduledJobUpdate,
  ): Promise<ScheduledJobResponse> {
    const response: ApiResponse<ScheduledJobResponse> = await apiClient.put(
      `/api/v1/scheduler/jobs/${job_id}`,
      data,
    )
    return response.data
  }

  /**
   * 删除特定计划任务
   * @param job_id 计划任务的job_id
   */
  static async deleteScheduledJob(job_id: string): Promise<ScheduledJobResponse> {
    const response: ApiResponse<ScheduledJobResponse> = await apiClient.delete(
      `/api/v1/scheduler/jobs/${job_id}`,
    )
    return response.data
  }

  /**
   * 切换特定计划任务的启用/禁用状态
   * @param job_id 计划任务的job_id
   */
  static async toggleScheduledJob(job_id: string): Promise<ScheduledJobResponse> {
    const response: ApiResponse<ScheduledJobResponse> = await apiClient.post(
      `/api/v1/scheduler/jobs/${job_id}/toggle`,
    )
    return response.data
  }
}
