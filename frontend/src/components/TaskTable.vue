<template>
  <div class="fade-in">
    <div v-if="isLoading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <p>正在加载任务...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="$emit('retry')" class="create-button">重试</button>
    </div>

    <div v-else-if="!Array.isArray(tasks) || tasks.length === 0" class="no-data-message">
      <p>🎯 暂无即时任务</p>
      <p style="margin-top: 0.5rem; font-size: 0.875rem; opacity: 0.7;">任务将在这里显示</p>
    </div>

    <div v-else class="task-table-container">
      <!-- 表头 -->
      <div class="task-table-header">
        <div class="header-cell task-info">任务信息</div>
        <div class="header-cell task-status">状态</div>
        <div class="header-cell task-progress">进度</div>
        <div class="header-cell task-time">时间</div>
        <div class="header-cell task-actions">操作</div>
      </div>

      <!-- 任务行 -->
      <div v-for="task in tasks" :key="task.id" class="task-row">
        <!-- 任务信息 -->
        <div class="task-cell task-info">
          <div class="task-primary">
            <span class="task-id">ID: {{ task.id }}</span>
            <span class="task-title">{{ getTaskTitle(task) }}</span>
          </div>
          <div class="task-secondary">
            <span class="task-type">{{ task.task_type }}</span>
            <span class="task-mode">{{ getParameter(task.parameters, 'mode') }}</span>
          </div>
        </div>

        <!-- 状态 -->
        <div class="task-cell task-status">
          <div class="status-badge" :class="`status-${task.status}`">
            <div class="status-dot"></div>
            <span>{{ getStatusText(task.status) }}</span>
          </div>
        </div>

        <!-- 进度 -->
        <div class="task-cell task-progress">
          <div v-if="task.status === 'running'" class="progress-container">
            <div class="progress-bar-small">
              <div class="progress-fill" :style="{ width: (task.percentage || 0) + '%' }"></div>
            </div>
            <div class="progress-text">
              <span class="progress-percentage">{{ (task.percentage || 0).toFixed(1) }}%</span>
              <span class="progress-items">{{ task.processed_items || 0 }}/{{ task.total_items || 0 }}</span>
            </div>
          </div>
          <div v-else class="progress-placeholder">-</div>
        </div>

        <!-- 时间 -->
        <div class="task-cell task-time">
          <div class="time-info">
            <div class="time-row">
              <span class="time-label">创建:</span>
              <span class="time-value">{{ formatDateTime(task.created_at) }}</span>
            </div>
            <div class="time-row" v-if="task.completed_at">
              <span class="time-label">完成:</span>
              <span class="time-value">{{ formatDateTime(task.completed_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 操作 -->
        <div class="task-cell task-actions">
          <button
            @click="onCancel(task.id)"
            :disabled="!canCancel(task.status)"
            class="action-btn"
            :class="{ 'action-btn-disabled': !canCancel(task.status) }"
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
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} 页</span>
        <button
          class="pagination-button"
          :disabled="tasks.length < pageSize"
          @click="$emit('page-change', currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TaskResponse } from '../services/crawlerApiService'
import { getParameter, formatDateTime, formatTime } from '../utils/taskUtils'

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
  const mode = getParameter(task.parameters, 'mode')
  if (mode === 'bangumi_id') {
    const bangumiId = getParameter(task.parameters, 'bangumi_id')
    return `番剧采集任务 (ID: ${bangumiId})`
  } else if (mode === 'url') {
    return '链接采集任务'
  } else if (mode === 'homepage') {
    return '首页采集任务'
  }
  return '采集任务'
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
.task-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.task-table-header {
  display: grid;
  grid-template-columns: 2.5fr 1.2fr 1.5fr 1.8fr 1fr;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
}

.header-cell {
  padding: 1.2rem 1rem;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  height: 60px; /* 固定表头高度 */
}

/* 表头对齐：与内容列保持一致 */
.header-cell:nth-child(1) { /* 任务信息 */
  justify-content: flex-start;
  padding-left: 1rem;
}

.header-cell:nth-child(2) { /* 状态 */
  justify-content: flex-start;
  padding-left: 1rem;
}

.header-cell:nth-child(3) { /* 进度 */
  justify-content: flex-start;
  padding-left: 1rem;
}

.header-cell:nth-child(4) { /* 时间 */
  justify-content: flex-start;
  padding-left: 1rem;
}

.header-cell:nth-child(5) { /* 操作 */
  border-right: none;
  justify-content: center;
  align-items: center; /* 确保操作列垂直居中 */
}

.task-row {
  display: grid;
  grid-template-columns: 2.5fr 1.2fr 1.5fr 1.8fr 1fr;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
  min-height: 90px;
}

.task-row:hover {
  background-color: #fafbfc;
}

.task-row:last-child {
  border-bottom: none;
}

.task-cell {
  padding: 1.2rem 1rem;
  display: flex;
  border-right: 1px solid #f0f0f0;
}

.task-cell:last-child {
  border-right: none;
  justify-content: center;
  align-items: center;
}

/* 任务信息列 */
.task-info {
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding-left: 1rem;
}

.task-primary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.task-secondary {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  width: 100%;
  align-items: center;
}

.task-id {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  font-family: 'Monaco', 'Menlo', monospace;
}

.task-title {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 600;
  line-height: 1.3;
}

.task-type, .task-mode {
  font-size: 0.7rem;
  color: #4b5563;
  padding: 0.35rem 0.75rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  min-width: 60px; /* 确保最小宽度一致 */
  height: 28px; /* 固定高度确保一致性 */
  text-align: center;
  line-height: 1; /* 确保文字垂直居中 */
}

.task-type:hover, .task-mode:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

/* 状态列 */
.task-status {
  justify-content: flex-start;
  align-items: center;
  padding-left: 1rem;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  border-radius: 18px;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid transparent;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-pending {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  color: #856404;
  border-color: #ffc107;
}

.status-pending .status-dot {
  background: #ffc107;
}

.status-running {
  background: linear-gradient(135deg, #d1ecf1 0%, #b3d7ff 100%);
  color: #0c5460;
  border-color: #17a2b8;
}

.status-running .status-dot {
  background: #17a2b8;
  animation: pulse 2s infinite;
}

.status-completed {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border-color: #28a745;
}

.status-completed .status-dot {
  background: #28a745;
}

.status-failed {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border-color: #dc3545;
}

.status-failed .status-dot {
  background: #dc3545;
}

.status-cancelled {
  background: linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%);
  color: #383d41;
  border-color: #6c757d;
}

.status-cancelled .status-dot {
  background: #6c757d;
}

/* 进度列 */
.task-progress {
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  padding-left: 1rem;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.progress-bar-small {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s ease;
  border-radius: 4px;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(255,255,255,0.3) 0%, transparent 100%);
  border-radius: 4px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-percentage {
  font-size: 0.8rem;
  font-weight: 700;
  color: #1f2937;
}

.progress-items {
  font-size: 0.75rem;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

.progress-placeholder {
  font-size: 0.875rem;
  color: #adb5bd;
  text-align: center;
  font-style: italic;
}

/* 时间列 */
.task-time {
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding-left: 1rem;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.time-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.time-label {
  font-size: 0.7rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.time-value {
  font-size: 0.8rem;
  color: #374151;
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 500;
}

/* 操作列 */
.action-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #dee2e6;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  color: #495057;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.action-btn:hover:not(.action-btn-disabled) {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-color: #adb5bd;
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
  color: #212529;
}

.action-btn-disabled {
  opacity: 0.6;
  cursor: not-allowed;
  color: #adb5bd;
  background: #f8f9fa;
  border-color: #e9ecef;
}

/* 分页控制器 */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.pagination-button {
  padding: 0.75rem 1.25rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  color: #495057;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-color: #adb5bd;
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
  color: #212529;
}

.pagination-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  background: #f8f9fa;
}

.page-info {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 600;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .task-table-header,
  .task-row {
    grid-template-columns: 2fr 1fr 1.2fr 1.5fr 0.8fr;
  }

  .header-cell,
  .task-cell {
    padding: 1rem 0.75rem;
  }

  .task-info {
    padding-left: 0.75rem;
  }

  .task-status,
  .task-progress,
  .task-time {
    padding-left: 0.75rem;
  }

  .task-title {
    font-size: 0.85rem;
  }

  .task-secondary {
    gap: 0.4rem;
  }

  .task-type, .task-mode {
    min-width: 50px;
    font-size: 0.65rem;
    padding: 0.25rem 0.6rem;
  }
}

@media (max-width: 768px) {
  .task-table-header {
    display: none;
  }

  .task-row {
    display: flex;
    flex-direction: column;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-bottom: 1rem;
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .task-cell {
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
    min-height: auto;
    padding: 1rem;
    flex-direction: column;
    align-items: flex-start !important;
  }

  .task-cell:last-child {
    border-bottom: none;
    justify-content: flex-start;
    align-items: flex-start !important;
  }

  .task-cell::before {
    content: attr(data-label);
    font-weight: 700;
    color: #6c757d;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: block;
  }

  .task-info::before { content: "任务信息"; }
  .task-status::before { content: "状态"; }
  .task-progress::before { content: "进度"; }
  .task-time::before { content: "时间"; }
  .task-actions::before { content: "操作"; }

  .task-secondary {
    gap: 0.5rem;
  }

  .task-type, .task-mode {
    min-width: 55px;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 加载和错误状态样式 */
.loading-indicator, .error-message, .no-data-message {
  text-align: center;
  padding: 3rem 2rem;
  color: #6c757d;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #dee2e6;
  border-top: 3px solid #17a2b8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.create-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
}

.create-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}
</style>
