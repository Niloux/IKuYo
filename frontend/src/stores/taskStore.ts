import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useFeedbackStore } from './feedbackStore'

import CrawlerApiService from '../services/crawler/crawlerApiService'
import type { CrawlerTaskCreate, TaskResponse } from '../services/crawler/crawlerTypes'
import ScheduledJobApiService from '../services/scheduler/schedulerApiService'
import type { ScheduledJobCreate, ScheduledJobResponse, ScheduledJobUpdate } from '../services/scheduler/schedulerTypes'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskResponse[]>([])
  const scheduledJobs = ref<ScheduledJobResponse[]>([])
  const isLoadingTasks = ref(false)
  const isLoadingScheduledJobs = ref(false)
  const error = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(10)

  // WebSocket连接管理
  const taskProgressWsMap = new Map<number, WebSocket>()

  // --- 即时任务相关操作 ---

  /**
   * 获取所有即时任务列表
   */
  const fetchTasks = async () => {
    const feedbackStore = useFeedbackStore()
    isLoadingTasks.value = true
    error.value = null
    try {
      tasks.value =
          await CrawlerApiService.listTasks(currentPage.value, pageSize.value)
    } catch (err: any) {
      error.value = err.message || '获取任务列表失败'
      feedbackStore.showError(error.value || '获取任务列表失败')
      console.error('获取任务列表失败:', err)
    } finally {
      isLoadingTasks.value = false
    }
  }

  /**
   * 设置当前页码
   */
  const setCurrentPage = (page: number) => {
  currentPage.value = page
  }

  /**
   * 创建新的即时任务
   * @param taskCreateData 任务创建数据
   */
  const createTask = async (taskCreateData: CrawlerTaskCreate) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const newTask = await CrawlerApiService.createTask(taskCreateData)
      await fetchTasks()
      return newTask
    } catch (err: any) {
      error.value = err.message || '创建任务失败'
      feedbackStore.showError(error.value || '创建任务失败')
      console.error('创建任务失败:', err)
      throw err
    }
  }

  /**
   * 取消即时任务
   * @param taskId 任务ID
   */
  const cancelTask = async (taskId: number) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const cancelledTask = await CrawlerApiService.cancelTask(taskId)
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = cancelledTask
      }
      return cancelledTask
    } catch (err: any) {
      error.value = err.message || '取消任务失败'
      feedbackStore.showError(error.value || '取消任务失败')
      console.error('取消任务失败:', err)
      throw err
    }
  }

  /**
   * 连接WebSocket获取任务进度
   * @param taskId 任务ID
   * @param onMessageCallback 接收到消息时的回调函数
   * @param onErrorCallback 发生错误时的回调函数
   * @param onCloseCallback 连接关闭时的回调函数
   */
  const connectTaskProgressWs = (
    taskId: number,
    onMessageCallback: (data: any) => void,
    onErrorCallback: (event: Event) => void,
    onCloseCallback: (event: CloseEvent) => void,
  ) => {
    const ws = CrawlerApiService.connectTaskProgressWs(taskId)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessageCallback(data)
      } catch (e) {
        console.error('WebSocket消息解析失败:', e)
      }
    }

    ws.onerror = (event) => {
      console.error('WebSocket错误:', event)
      onErrorCallback(event)
    }

    ws.onclose = (event) => {
      console.log('WebSocket连接关闭:', event)
      onCloseCallback(event)
    }

    return ws
  }

  // --- 定时任务相关操作 ---

  /**
   * 获取所有计划任务列表
   */
  const fetchScheduledJobs = async () => {
    const feedbackStore = useFeedbackStore()
    isLoadingScheduledJobs.value = true
    error.value = null
    try {
      scheduledJobs.value = await ScheduledJobApiService.listScheduledJobs()
    } catch (err: any) {
      error.value = err.message || '获取计划任务列表失败'
      feedbackStore.showError(error.value || '获取计划任务列表失败')
      console.error('获取计划任务列表失败:', err)
    } finally {
      isLoadingScheduledJobs.value = false
    }
  }

  /**
   * 创建新的计划任务
   * @param jobCreateData 计划任务创建数据
   */
  const createScheduledJob = async (jobCreateData: ScheduledJobCreate) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const newJob =
        await ScheduledJobApiService.createScheduledJob(jobCreateData)
      await fetchScheduledJobs()
      return newJob
    } catch (err: any) {
      error.value = err.message || '创建计划任务失败'
      feedbackStore.showError(error.value || '创建计划任务失败')
      console.error('创建计划任务失败:', err)
      throw err
    }
  }

  /**
   * 更新计划任务
   * @param job_id 任务ID
   * @param jobUpdateData 计划任务更新数据
   */
  const updateScheduledJob = async (
    job_id: string,
    jobUpdateData: ScheduledJobUpdate,
  ) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const updatedJob = await ScheduledJobApiService.updateScheduledJob(
        job_id,
        jobUpdateData,
      )
      await fetchScheduledJobs()
      return updatedJob
    } catch (err: any) {
      error.value = err.message || '更新计划任务失败'
      feedbackStore.showError(error.value || '更新计划任务失败')
      console.error('更新计划任务失败:', err)
      throw err
    }
  }

  /**
   * 删除计划任务
   * @param job_id 任务ID
   */
  const deleteScheduledJob = async (job_id: string) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const deletedJob = await ScheduledJobApiService.deleteScheduledJob(job_id)
      await fetchScheduledJobs()
      return deletedJob
    } catch (err: any) {
      error.value = err.message || '删除计划任务失败'
      feedbackStore.showError(error.value || '删除计划任务失败')
      console.error('删除计划任务失败:', err)
      throw err
    }
  }

  /**
   * 切换计划任务启用/禁用状态
   * @param job_id 任务ID
   */
  const toggleScheduledJob = async (job_id: string) => {
    const feedbackStore = useFeedbackStore()
    error.value = null
    try {
      const toggledJob = await ScheduledJobApiService.toggleScheduledJob(job_id)
      await fetchScheduledJobs()
      return toggledJob
    } catch (err: any) {
      error.value = err.message || '切换计划任务状态失败'
      feedbackStore.showError(error.value || '切换计划任务状态失败')
      console.error('切换计划任务状态失败:', err)
      throw err
    }
  }

  /**
   * 启动某个任务的WebSocket进度监听
   * @param taskId 任务ID
   */
  const startTaskProgressWs = (
    taskId: number,
    onErrorCallback?: (event: Event) => void,
    onCloseCallback?: (event: CloseEvent) => void,
  ) => {
    // 已存在则不重复连接
    if (taskProgressWsMap.has(taskId)) return
    const ws = CrawlerApiService.connectTaskProgressWs(taskId)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // 更新tasks中对应任务的进度
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = { ...tasks.value[index], ...data }
          // 任务完成/失败/取消时自动断开
          if (["completed", "failed", "cancelled"].includes(data.status)) {
            stopTaskProgressWs(taskId)
          }
        }
      } catch (e) {
        console.error('WebSocket消息解析失败:', e)
      }
    }
    ws.onerror = (event) => {
      console.error('WebSocket错误:', event)
      stopTaskProgressWs(taskId)
      if (onErrorCallback) onErrorCallback(event)
      // 可选：回退为定时fetchTasks
      fetchTasks()
    }
    ws.onclose = (event) => {
      console.log('WebSocket连接关闭:', event)
      stopTaskProgressWs(taskId)
      if (onCloseCallback) onCloseCallback(event)
    }
    taskProgressWsMap.set(taskId, ws)
  }

  /**
   * 停止某个任务的WebSocket进度监听
   * @param taskId 任务ID
   */
  const stopTaskProgressWs = (taskId: number) => {
    const ws = taskProgressWsMap.get(taskId)
    if (ws) {
      ws.close()
      taskProgressWsMap.delete(taskId)
    }
  }

  /**
   * 停止所有任务的WebSocket进度监听
   */
  const stopAllTaskProgressWs = () => {
    for (const [taskId, ws] of taskProgressWsMap.entries()) {
      ws.close()
    }
    taskProgressWsMap.clear()
  }

  return {
  tasks, scheduledJobs, isLoadingTasks, isLoadingScheduledJobs, error,
      currentPage, pageSize, fetchTasks, setCurrentPage, createTask, cancelTask,
      connectTaskProgressWs, startTaskProgressWs, stopTaskProgressWs,
      stopAllTaskProgressWs, fetchScheduledJobs, createScheduledJob,
      updateScheduledJob, deleteScheduledJob, toggleScheduledJob,
  }
})
