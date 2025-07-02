<template>
  <div class="task-management-view">
    <div class="task-section">
      <TaskTable
        :tasks="taskStore.tasks"
        :isLoading="taskStore.isLoadingTasks"
        :error="taskStore.error"
        :onCancel="cancelTask"
      />
    </div>
    <div class="task-section">
      <div class="section-header">
        <span class="section-title">定时任务</span>
        <button @click="openCreateScheduledJobModal" class="create-button">新建</button>
      </div>
      <div class="section-content">
        <ScheduledJobTable
          :jobs="taskStore.scheduledJobs"
          :isLoading="taskStore.isLoadingScheduledJobs"
          :error="taskStore.error"
          :onEdit="editScheduledJob"
          :onDelete="deleteScheduledJob"
          :onToggle="toggleScheduledJob"
        />
      </div>
    </div>

    <TaskModal
      :visible="showCreateTaskModal"
      :task="newTask"
      :errors="createTaskFormErrors"
      :onSubmit="submitCreateTask"
      :onCancel="closeCreateTaskModal"
      :onUpdateTask="(t) => { newTask = t }"
    />

    <ScheduledJobModal
      :visible="showScheduledJobModal"
      :job="currentScheduledJob"
      :errors="scheduledJobFormErrors"
      :editing="!!editingJob"
      :onSubmit="submitScheduledJob"
      :onCancel="closeScheduledJobModal"
      :onUpdateJob="(j) => { currentScheduledJob = j }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useTaskStore } from '../stores/taskStore'
import TaskTable from '../components/TaskTable.vue'
import ScheduledJobTable from '../components/ScheduledJobTable.vue'
import TaskModal from '../components/TaskModal.vue'
import ScheduledJobModal from '../components/ScheduledJobModal.vue'
import type { ScheduledJobResponse, CrawlerTaskCreate, TaskResponse, ScheduledJobCreate, ScheduledJobUpdate } from '../services/crawlerApiService'

const taskStore = useTaskStore()

const showCreateTaskModal = ref(false)
const showScheduledJobModal = ref(false)
const editingJob = ref<ScheduledJobResponse | null>(null)

// 新任务表单数据
const newTask = ref<CrawlerTaskCreate & { bangumi_id?: number }>({
  mode: '',
  bangumi_id: undefined,
  year: undefined,
  season: undefined,
  start_url: undefined,
  limit: undefined,
})

// 定时任务表单数据
const currentScheduledJob = ref<ScheduledJobCreate & { parameters_json?: string }>({
  job_id: '',
  name: '',
  cron_expression: '',
  parameters: {},
  parameters_json: '{}',
  enabled: true,
  description: '',
})

// WebSocket连接实例
const activeWebSockets = ref<Map<number, WebSocket>>(new Map())

// WebSocket进度监听相关
const wsEnabled = ref(true) // 可用于后续切换WebSocket/轮询

// 监听进行中任务，自动建立WebSocket连接
watch(
  () => (Array.isArray(taskStore.tasks) ? taskStore.tasks : []).map(t => ({ id: t.id, status: t.status })),
  (newTasks) => {
    if (!wsEnabled.value) return
    newTasks.forEach(task => {
      if (["pending", "running"].includes(task.status)) {
        taskStore.startTaskProgressWs(task.id)
      } else {
        taskStore.stopTaskProgressWs(task.id)
      }
    })
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  taskStore.fetchTasks()
  taskStore.fetchScheduledJobs()
  // 可选：定时轮询作为兜底
  // setInterval(() => { if (!wsEnabled.value) taskStore.fetchTasks() }, 10000)
})

onUnmounted(() => {
  taskStore.stopAllTaskProgressWs()
})

const openCreateTaskModal = () => {
  // 重置表单
  newTask.value = {
    mode: '',
    bangumi_id: undefined,
    year: undefined,
    season: undefined,
    start_url: undefined,
    limit: undefined,
  }
  showCreateTaskModal.value = true
}

const closeCreateTaskModal = () => {
  showCreateTaskModal.value = false
}

const createTaskFormErrors = ref<{ [key: string]: string }>({})
const scheduledJobFormErrors = ref<{ [key: string]: string }>({})

function validateCreateTaskForm() {
  createTaskFormErrors.value = {}
  if (!newTask.value.mode) {
    createTaskFormErrors.value.mode = '请选择模式'
  }
  if (newTask.value.mode === 'bangumi_id' && (!newTask.value.bangumi_id || newTask.value.bangumi_id <= 0)) {
    createTaskFormErrors.value.bangumi_id = '请输入有效的番剧ID'
  }
  if (newTask.value.mode === 'url' && !newTask.value.start_url) {
    createTaskFormErrors.value.start_url = '请输入起始URL'
  }
  if (newTask.value.limit !== undefined && newTask.value.limit !== null && (!Number.isInteger(newTask.value.limit) || newTask.value.limit <= 0)) {
    createTaskFormErrors.value.limit = '请输入正整数或留空'
  }
  return Object.keys(createTaskFormErrors.value).length === 0
}

function validateScheduledJobForm() {
  scheduledJobFormErrors.value = {}
  if (!currentScheduledJob.value.job_id) {
    scheduledJobFormErrors.value.job_id = '请输入任务ID'
  }
  if (!currentScheduledJob.value.name) {
    scheduledJobFormErrors.value.name = '请输入名称'
  }
  if (!currentScheduledJob.value.cron_expression) {
    scheduledJobFormErrors.value.cron_expression = '请输入Cron表达式'
  }
  if (currentScheduledJob.value.parameters_json) {
    try {
      JSON.parse(currentScheduledJob.value.parameters_json)
    } catch {
      scheduledJobFormErrors.value.parameters_json = '参数需为合法JSON'
    }
  }
  return Object.keys(scheduledJobFormErrors.value).length === 0
}

const submitCreateTask = async () => {
  if (!validateCreateTaskForm()) return
  try {
    // 根据mode调整发送的参数
    const payload: CrawlerTaskCreate = {
      mode: newTask.value.mode,
      limit: newTask.value.limit,
    }
    // @ts-ignore
    if (newTask.value.mode === 'bangumi_id') {
      // @ts-ignore
      payload.bangumi_id = newTask.value.bangumi_id
    } else if (newTask.value.mode === 'url') {
      payload.start_url = newTask.value.start_url
    }

    const createdTask = await taskStore.createTask(payload)
    alert(`任务创建成功！ID: ${createdTask.id}`)
    closeCreateTaskModal()
    // 如果新任务是运行中或待处理状态，建立WebSocket连接
    if (createdTask.status === 'running' || createdTask.status === 'pending') {
      setupTaskWebSocket(createdTask.id)
    }
  } catch (e: any) {
    alert(`创建任务失败: ${e.value.message}`)
  }
}

const openCreateScheduledJobModal = () => {
  editingJob.value = null
  // 重置表单
  currentScheduledJob.value = {
    job_id: '',
    name: '',
    cron_expression: '',
    parameters: {},
    parameters_json: '{}',
    enabled: true,
    description: '',
  }
  showScheduledJobModal.value = true
}

const closeScheduledJobModal = () => {
  showScheduledJobModal.value = false
}

const editScheduledJob = (job: ScheduledJobResponse) => {
  editingJob.value = job
  // 填充表单数据
  currentScheduledJob.value = {
    job_id: job.job_id,
    name: job.name,
    cron_expression: job.cron_expression,
    parameters: job.parameters,
    parameters_json: JSON.stringify(job.parameters, null, 2), // 格式化JSON字符串
    enabled: job.enabled,
    description: job.description || '',
  }
  showScheduledJobModal.value = true
}

const submitScheduledJob = async () => {
  if (!validateScheduledJobForm()) return
  try {
    // 解析JSON参数
    let parsedParameters = {}
    if (currentScheduledJob.value.parameters_json) {
      try {
        parsedParameters = JSON.parse(currentScheduledJob.value.parameters_json)
      } catch (e) {
        alert('参数JSON格式不正确！')
        return
      }
    }

    const payload = {
      job_id: currentScheduledJob.value.job_id,
      name: currentScheduledJob.value.name,
      cron_expression: currentScheduledJob.value.cron_expression,
      parameters: parsedParameters,
      enabled: currentScheduledJob.value.enabled,
      description: currentScheduledJob.value.description,
    }

    if (editingJob.value) {
      // 更新现有任务
      await taskStore.updateScheduledJob(editingJob.value.job_id, payload as ScheduledJobUpdate)
      alert('定时任务更新成功！')
    } else {
      // 创建新任务
      await taskStore.createScheduledJob(payload as ScheduledJobCreate)
      alert('定时任务创建成功！')
    }
    closeScheduledJobModal()
  } catch (e: any) {
    alert(`操作失败: ${e.message}`)
  }
}

const cancelTask = async (taskId: number) => {
  if (confirm('确定要取消这个任务吗？')) {
    try {
      const cancelledTask = await taskStore.cancelTask(taskId)
      alert('任务已取消！')
      // 如果任务被取消，关闭对应的WebSocket连接
      if (activeWebSockets.value.has(taskId)) {
        activeWebSockets.value.get(taskId)?.close()
        activeWebSockets.value.delete(taskId)
      }
    } catch (e: any) {
      alert(`取消任务失败: ${e.message}`)
    }
  }
}

const toggleScheduledJob = async (jobId: string) => {
  try {
    await taskStore.toggleScheduledJob(jobId)
    alert('定时任务状态已更新！')
  } catch (e: any) {
    alert(`更新定时任务状态失败: ${e.message}`)
  }
}

const deleteScheduledJob = async (jobId: string) => {
  if (confirm('确定要删除这个定时任务吗？')) {
    try {
      await taskStore.deleteScheduledJob(jobId)
      alert('定时任务已删除！')
    } catch (e: any) {
      alert(`删除定时任务失败: ${e.message}`)
    }
  }
}

// 设置任务WebSocket连接
const setupTaskWebSocket = (taskId: number) => {
  if (activeWebSockets.value.has(taskId)) {
    // 如果已经有连接，则不重复建立
    return
  }

  const ws = taskStore.connectTaskProgressWs(
    taskId,
    (data: any) => {
      // 收到WebSocket消息时更新任务状态
      const index = taskStore.tasks.findIndex(t => t.id === taskId)
      if (index !== -1) {
        // 确保只更新WebSocket发送的字段，避免覆盖其他字段
        taskStore.tasks[index] = { ...taskStore.tasks[index], ...data }
      }
    },
    (event: Event) => {
      console.error(`任务 ${taskId} 的WebSocket连接错误:`, event)
      // 可以在这里处理错误，例如显示错误信息
    },
    (event: CloseEvent) => {
      console.log(`任务 ${taskId} 的WebSocket连接关闭:`, event)
      activeWebSockets.value.delete(taskId)
      // 如果连接是正常关闭（例如任务完成），可以不显示错误
      // 如果是非正常关闭，可以尝试重新连接或显示提示
      if (event.code !== 1000) { // 1000是正常关闭
        console.warn(`任务 ${taskId} 的WebSocket连接异常关闭，尝试重新获取任务状态...`)
        // 重新获取任务状态以确保显示最新状态
        taskStore.fetchTasks()
      }
    },
  )
  activeWebSockets.value.set(taskId, ws)
}

// 辅助函数：从parameters字符串中解析特定参数
const getParameter = (parameters: string | undefined, key: string): string => {
  if (!parameters) return '-'
  try {
    const params = JSON.parse(parameters)
    // 特殊处理bangumi_id，因为后端可能直接返回bangumi_id而不是parameters中的mode
    if (key === 'mode' && params.bangumi_id) {
      return `bangumi_id: ${params.bangumi_id}`
    }
    return params[key] || '-'
  } catch (e) {
    console.error('解析参数失败:', e)
    return '-'
  }
}

// 辅助函数：格式化日期时间
const formatDateTime = (dateTimeStr: string | undefined): string => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString()
}

// 辅助函数：格式化秒为可读时间
const formatTime = (seconds: number | undefined): string => {
  if (seconds === undefined || seconds < 0) return '-'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}
</script>

<style src="../assets/task.css"></style>
<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
  margin-bottom: 10px;
  padding-top: 8px;
}
.section-title {
  font-size: 1.13em;
  color: #666;
  font-weight: 500;
  letter-spacing: 0.01em;
  margin-left: 2px;
}
.section-content {
  margin-bottom: 32px;
  margin-top: 8px;
}
.task-section:first-child .section-header {
  margin-top: 12px;
}
</style>
