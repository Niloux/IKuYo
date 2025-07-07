import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAsyncAction } from './asyncUtils'

import CrawlerApiService from '../services/crawler/crawlerApiService'
import type { CrawlerTaskCreate, TaskResponse } from '../services/crawler/crawlerTypes'

/**
 * Pinia 即时任务管理 Store
 * 专注管理即时任务相关状态、异步操作和WebSocket进度
 * 定时任务请使用 schedulerStore
 */
export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskResponse[]>([])
  const currentPage = ref(1)
  const pageSize = ref(10)
  // WebSocket连接管理
  const taskProgressWsMap = new Map<number, WebSocket>()

  // --- 即时任务相关操作 ---
  /**
   * 获取所有即时任务列表
   * @returns Promise<TaskResponse[]>
   */
  const fetchTasksAsync = useAsyncAction(() => CrawlerApiService.listTasks(currentPage.value, pageSize.value))
  const fetchTasks = async () => {
    const result = await fetchTasksAsync.run()
    tasks.value = result
    return result
  }

  /**
   * 创建新的即时任务
   * @param taskCreateData 任务创建数据
   * @returns Promise<TaskResponse>
   */
  const createTaskAsync = useAsyncAction((taskCreateData: CrawlerTaskCreate) => CrawlerApiService.createTask(taskCreateData))
  const createTask = async (taskCreateData: CrawlerTaskCreate) => {
    const result = await createTaskAsync.run(taskCreateData)
    await fetchTasks()
    return result
  }

  /**
   * 取消即时任务
   * @param taskId 任务ID
   * @returns Promise<TaskResponse>
   */
  const cancelTaskAsync = useAsyncAction((taskId: number) => CrawlerApiService.cancelTask(taskId))
  const cancelTask = async (taskId: number) => {
    const result = await cancelTaskAsync.run(taskId)
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value[index] = result
    }
    return result
  }

  // --- WebSocket 相关操作 ---
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
    // 状态
    tasks,
    currentPage,
    pageSize,

    // 即时任务操作
    fetchTasks,
    createTask,
    cancelTask,

    // 异步状态
    fetchTasksAsync,
    createTaskAsync,
    cancelTaskAsync,

    // WebSocket操作
    connectTaskProgressWs,
    startTaskProgressWs,
    stopTaskProgressWs,
    stopAllTaskProgressWs
  }
})
