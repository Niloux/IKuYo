<template>
  <div class="fade-in">
    <div v-if="isLoading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <p>正在加载定时任务...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="$emit('retry')" class="create-button">重试</button>
    </div>

    <div v-else-if="!Array.isArray(jobs) || jobs.length === 0" class="no-data-message">
      <p>⏰ 暂无定时任务</p>
      <p style="margin-top: 0.5rem; font-size: 0.875rem; opacity: 0.7;">创建定时任务来自动化您的工作流程</p>
    </div>

    <div v-else class="task-list-container">
      <div v-for="job in jobs" :key="job.job_id" class="scheduled-job-card">
        <!-- 启用/禁用开关 -->
        <div class="job-enabled-toggle">
          <label class="toggle-switch">
            <input
              type="checkbox"
              :checked="job.enabled"
              @change="onToggle(job.job_id)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- 任务状态指示器 -->
        <div class="task-status" :class="job.enabled ? 'status-running' : 'status-cancelled'">
          <div class="status-dot"></div>
          <span>{{ job.enabled ? '已启用' : '已禁用' }}</span>
        </div>

        <!-- 任务头部信息 -->
        <div class="task-header">
          <div class="task-id">{{ job.job_id }}</div>
        </div>

        <!-- 任务标题和描述 -->
        <div class="task-title">
          {{ job.name }}
        </div>
        <div class="task-mode" v-if="job.description">
          {{ job.description }}
        </div>

        <!-- Cron表达式 -->
        <div class="cron-expression">
          <div class="task-meta-label">执行计划</div>
          <code>{{ job.cron_expression }}</code>
          <div class="cron-description">{{ getCronDescription(job.cron_expression) }}</div>
        </div>

        <!-- 参数信息 -->
        <div v-if="job.parameters && Object.keys(job.parameters).length > 0" class="task-meta">
          <div class="task-meta-item">
            <span class="task-meta-label">执行参数</span>
            <div class="parameters-display">
              <pre>{{ formatParameters(job.parameters) }}</pre>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="task-actions">
          <button @click="onEdit(job)" class="action-button edit-button">
            编辑
          </button>
          <button @click="onDelete(job.job_id)" class="action-button delete-button">
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ScheduledJobResponse } from '../services/crawlerApiService'

defineProps<{
  jobs: ScheduledJobResponse[]
  isLoading: boolean
  error: string | null
  onEdit: (job: ScheduledJobResponse) => void
  onDelete: (jobId: string) => void
  onToggle: (jobId: string) => void
}>()

defineEmits<{
  retry: []
}>()

// 格式化参数显示
const formatParameters = (parameters: any): string => {
  if (!parameters || Object.keys(parameters).length === 0) {
    return '无'
  }
  return JSON.stringify(parameters, null, 2)
}

// 获取Cron表达式描述
const getCronDescription = (cronExpression: string): string => {
  // 简单的Cron表达式描述映射
  const commonCronMap: { [key: string]: string } = {
    '0 0 * * *': '每天午夜执行',
    '0 */1 * * *': '每小时执行',
    '0 */6 * * *': '每6小时执行',
    '0 */12 * * *': '每12小时执行',
    '0 0 */1 * *': '每天执行',
    '0 0 */7 * *': '每周执行',
    '0 0 1 * *': '每月1日执行',
    '0 0 * * 0': '每周日执行',
    '0 0 * * 1': '每周一执行',
    '*/30 * * * *': '每30分钟执行',
    '*/15 * * * *': '每15分钟执行',
    '*/10 * * * *': '每10分钟执行',
    '*/5 * * * *': '每5分钟执行'
  }

  return commonCronMap[cronExpression] || '自定义计划'
}
</script>

<style src="../assets/task.css"></style>
<style scoped>
.cron-description {
  font-size: 0.75rem;
  color: var(--color-text-light);
  margin-top: 0.25rem;
}

.parameters-display {
  margin-top: 0.5rem;
}

.parameters-display pre {
  background: var(--color-bg-light);
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
