<template>
  <div class="fade-in">
    <Skeleton :loading="isLoading" type="list" :rows="4" customClass="task-table-skeleton" />
    <div v-if="!isLoading && error" class="error-message">
      <p>{{ error }}</p>
      <button @click="$emit('retry')" class="retry-button">重试</button>
    </div>

    <div v-else-if="!Array.isArray(tasks) || tasks.length === 0" class="no-data-message">
      <p>🎯 暂无即时任务</p>
      <p style="margin-top: 0.5rem; font-size: 0.875rem; opacity: 0.7;">任务将在这里显示</p>
    </div>

    <div v-else class="task-grid">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="task-header">
          <span class="task-id">#{{ task.id }}</span>
          <div class="status-badge" :class="`status-${task.status}`">
            <div class="status-dot"></div>
            <span>{{ getStatusText(task.status) }}</span>
          </div>
        </div>

        <h4 class="task-title">{{ getTaskTitle(task) }}</h4>

        <div class="task-meta-items">
          <div class="task-meta-item">
            <span class="task-meta-label">类型</span>
            <span class="task-meta-value">{{ task.task_type }}</span>
          </div>
          <div class="task-meta-item">
            <span class="task-meta-label">模式</span>
            <span class="task-meta-value">{{ getParameter(task.parameters, 'mode') }}</span>
          </div>
          <div class="task-meta-item">
            <span class="task-meta-label">创建时间</span>
            <span class="task-meta-value">{{ formatDateTime(task.created_at) }}</span>
          </div>
        </div>

        <div class="progress-section" v-if="task.status === 'running'">
          <div class="progress-header">
            <span class="progress-percentage">{{ (task.percentage || 0).toFixed(1) }}%</span>
            <span class="progress-details">{{ formatTime(task.estimated_remaining || 0) }}</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: (task.percentage || 0) + '%' }"></div>
          </div>
        </div>

        <div class="task-actions">
          <button
            @click="onCancel(task.id)"
            :disabled="!canCancel(task.status)"
            class="action-button cancel-button"
            :class="{ 'disabled': !canCancel(task.status) }"
          >
            {{ getCancelButtonText(task.status) }}
          </button>
        </div>
      </div>

      <!-- 分页控制器 -->
      <div class="pagination-controls" v-if="tasks.length > 0">
        <button
          class="pagination-button"
          :disabled="currentPage === 1"
          @click="$emit('page-change', currentPage - 1)"
        >
          ← 上一页
        </button>
        <span class="page-info">第 {{ currentPage }} 页</span>
        <button
          class="pagination-button"
          :disabled="tasks.length < pageSize"
          @click="$emit('page-change', currentPage + 1)"
        >
          下一页 →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TaskResponse } from '../services/crawler/crawlerTypes'
import { getParameter, formatDateTime, formatTime } from '../utils/taskUtils'
import Skeleton from './common/Skeleton.vue'
import { defineAsyncComponent } from 'vue'

const props = defineProps<{
  tasks: TaskResponse[]
  isLoading: boolean
  error: string | null
  onCancel: (taskId: number) => void
  currentPage: number
  pageSize: number
}>()

const emit = defineEmits<{
  retry: []
  'page-change': [page: number]
}>()

const TaskModal = defineAsyncComponent(() => import('./TaskModal.vue'))
const ScheduledJobModal = defineAsyncComponent(() => import('./ScheduledJobModal.vue'))

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: { [key: string]: string } = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 获取任务标题
const getTaskTitle = (task: TaskResponse): string => {
  if (!task.parameters) return '采集任务'

  try {
    const params = JSON.parse(task.parameters)
    const mode = params.mode

    switch (mode) {
      case 'homepage':
        return '首页采集任务'
      case 'season':
        return `季度采集任务 (${params.year || ''}年${params.season || ''})`
      case 'year':
        return `年份采集任务 (${params.year || ''}年)`
      default:
        return '采集任务'
    }
  } catch (e) {
    console.error('解析任务参数失败:', e)
    return '采集任务'
  }
}

// 判断是否可以取消
const canCancel = (status: string): boolean => {
  return ['pending', 'running'].includes(status)
}

// 获取取消按钮文本
const getCancelButtonText = (status: string): string => {
  if (canCancel(status)) {
    return '取消'
  }
  return '已完成'
}
</script>

<style scoped>
/* 任务网格布局 */
.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 1.5rem; /* 与首页的 day-section 保持一致的内边距 */
}

/* 任务卡片样式 */
.task-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg); /* 使用更大的圆角 */
  padding: 1.5rem;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* 使内容在垂直方向上分散 */
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.task-id {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-light);
  background: var(--color-bg-light);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-pending {
  background: #fef3c7;
  color: #d97706;
}

.status-pending .status-dot {
  background: #f59e0b;
}

.status-running {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-running .status-dot {
  background: #3b82f6;
  animation: pulse 2s infinite;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-completed .status-dot {
  background: #10b981;
}

.status-failed {
  background: #fee2e2;
  color: #dc2626;
}

.status-failed .status-dot {
  background: #ef4444;
}

.status-cancelled {
  background: #f3f4f6;
  color: #6b7280;
}

.status-cancelled .status-dot {
  background: #9ca3af;
}

.task-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 1rem;
}

.task-meta-items {
  display: grid;
  grid-template-columns: 1fr 1fr; /* 两列布局 */
  gap: 0.75rem 1rem; /* 行间距和列间距 */
  margin-bottom: 1.5rem;
}

.task-meta-item {
  display: flex;
  flex-direction: column;
}

.task-meta-label {
  font-size: 0.75rem;
  color: var(--color-text-light);
  text-transform: uppercase;
  font-weight: 500;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.task-meta-value {
  font-size: 0.875rem;
  color: var(--color-text-dark);
  font-weight: 500;
}

/* 进度条样式 */
.progress-section {
  margin-top: auto; /* 将进度条推到底部 */
  margin-bottom: 1rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-percentage {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-primary);
}

.progress-details {
  font-size: 0.75rem;
  color: var(--color-text-light);
}

.progress-bar-container {
  position: relative;
  height: 8px;
  background: var(--color-bg-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(45deg, var(--color-primary), var(--color-primary-light));
  border-radius: var(--radius-sm);
  transition: width 0.3s ease;
}

/* 操作按钮 */
.task-actions {
  margin-top: 1rem;
}

.action-button {
  width: 100%; /* 按钮宽度占满 */
  padding: 0.75rem 1rem;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.cancel-button {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.cancel-button:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.2);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 分页控制器 */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--color-bg-white);
  border-top: 1px solid var(--color-border-light);
  grid-column: 1 / -1; /* 占据所有列 */
  border-radius: 0 0 var(--radius-lg) var(--radius-lg); /* 底部圆角 */
  box-shadow: var(--shadow-md);
  margin-top: 1.5rem;
}

.pagination-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg-white);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pagination-button:hover:not(:disabled) {
  background: var(--color-bg-light);
  border-color: var(--color-primary);
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.875rem;
  color: var(--color-text-light);
  font-weight: 500;
}

/* 加载和错误状态 */
.loading-indicator, .error-message, .no-data-message {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--color-text-light);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.retry-button {
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.retry-button:hover {
  background: var(--color-primary-dark);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-grid {
    grid-template-columns: 1fr;
    padding: 1rem;
    gap: 1rem;
  }

  .task-card {
    padding: 1rem;
  }

  .task-meta-items {
    grid-template-columns: 1fr; /* 小屏幕下改为单列 */
  }

  .pagination-controls {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
