import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAsyncAction } from './asyncUtils'

import CrawlerApiService from '../services/crawler/crawlerApiService'
import type { CrawlerTaskCreate, TaskResponse } from '../services/crawler/crawlerTypes'
import ScheduledJobApiService from '../services/scheduler/schedulerApiService'
import type { ScheduledJobCreate, ScheduledJobResponse, ScheduledJobUpdate } from '../services/scheduler/schedulerTypes'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskResponse[]>([])
  const scheduledJobs = ref<ScheduledJobResponse[]>([])
  const currentPage = ref(1)
  const pageSize = ref(10)
  // WebSocket连接管理
  const taskProgressWsMap = new Map<number, WebSocket>()

  // --- 即时任务相关操作 ---
  // 获取所有即时任务列表
  const fetchTasksAsync = useAsyncAction(() => CrawlerApiService.listTasks(currentPage.value, pageSize.value))
  const fetchTasks = async () => {
    const result = await fetchTasksAsync.run()
    tasks.value = result
    return result
  }

  // 创建新的即时任务
  const createTaskAsync = useAsyncAction((taskCreateData: CrawlerTaskCreate) => CrawlerApiService.createTask(taskCreateData))
  const createTask = async (taskCreateData: CrawlerTaskCreate) => {
    const result = await createTaskAsync.run(taskCreateData)
    await fetchTasks()
    return result
  }

  // 取消即时任务
  const cancelTaskAsync = useAsyncAction((taskId: number) => CrawlerApiService.cancelTask(taskId))
  const cancelTask = async (taskId: number) => {
    const result = await cancelTaskAsync.run(taskId)
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value[index] = result
    }
    return result
  }

  // --- 定时任务相关操作 ---
  // 获取所有计划任务列表
  const fetchScheduledJobsAsync = useAsyncAction(() => ScheduledJobApiService.listScheduledJobs())
  const fetchScheduledJobs = async () => {
    const result = await fetchScheduledJobsAsync.run()
    scheduledJobs.value = result
    return result
  }

  // 创建新的计划任务
  const createScheduledJobAsync = useAsyncAction((jobCreateData: ScheduledJobCreate) => ScheduledJobApiService.createScheduledJob(jobCreateData))
  const createScheduledJob = async (jobCreateData: ScheduledJobCreate) => {
    const result = await createScheduledJobAsync.run(jobCreateData)
    await fetchScheduledJobs()
    return result
  }

  // 更新计划任务
  const updateScheduledJobAsync = useAsyncAction((job_id: string, jobUpdateData: ScheduledJobUpdate) => ScheduledJobApiService.updateScheduledJob(job_id, jobUpdateData))
  const updateScheduledJob = async (job_id: string, jobUpdateData: ScheduledJobUpdate) => {
    const result = await updateScheduledJobAsync.run(job_id, jobUpdateData)
    await fetchScheduledJobs()
    return result
  }

  // 删除计划任务
  const deleteScheduledJobAsync = useAsyncAction((job_id: string) => ScheduledJobApiService.deleteScheduledJob(job_id))
  const deleteScheduledJob = async (job_id: string) => {
    const result = await deleteScheduledJobAsync.run(job_id)
    await fetchScheduledJobs()
    return result
  }

  // 切换计划任务启用/禁用状态
  const toggleScheduledJobAsync = useAsyncAction((job_id: string) => ScheduledJobApiService.toggleScheduledJob(job_id))
  const toggleScheduledJob = async (job_id: string) => {
    const result = await toggleScheduledJobAsync.run(job_id)
    await fetchScheduledJobs()
    return result
  }

  // WebSocket相关逻辑保持不变
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

  const startTaskProgressWs = (
    taskId: number,
    onErrorCallback?: (event: Event) => void,
    onCloseCallback?: (event: CloseEvent) => void,
  ) => {
    if (taskProgressWsMap.has(taskId)) return
    const ws = CrawlerApiService.connectTaskProgressWs(taskId)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) {
          tasks.value[index] = { ...tasks.value[index], ...data }
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
      fetchTasks()
    }
    ws.onclose = (event) => {
      console.log('WebSocket连接关闭:', event)
      stopTaskProgressWs(taskId)
      if (onCloseCallback) onCloseCallback(event)
    }
    taskProgressWsMap.set(taskId, ws)
  }

  const stopTaskProgressWs = (taskId: number) => {
    const ws = taskProgressWsMap.get(taskId)
    if (ws) {
      ws.close()
      taskProgressWsMap.delete(taskId)
    }
  }

  const stopAllTaskProgressWs = () => {
    for (const [taskId, ws] of taskProgressWsMap.entries()) {
      ws.close()
    }
    taskProgressWsMap.clear()
  }

  return {
    tasks, scheduledJobs, currentPage, pageSize,
    fetchTasks, createTask, cancelTask,
    fetchScheduledJobs, createScheduledJob, updateScheduledJob, deleteScheduledJob, toggleScheduledJob,
    fetchTasksAsync, createTaskAsync, cancelTaskAsync,
    fetchScheduledJobsAsync, createScheduledJobAsync, updateScheduledJobAsync, deleteScheduledJobAsync, toggleScheduledJobAsync,
    connectTaskProgressWs, startTaskProgressWs, stopTaskProgressWs, stopAllTaskProgressWs
  }
})
