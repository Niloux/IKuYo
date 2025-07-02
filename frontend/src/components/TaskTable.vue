<template>
  <div>
    <div v-if="isLoading" class="loading-indicator">加载中...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else-if="!Array.isArray(tasks) || tasks.length === 0" class="no-data-message">暂无即时任务。</div>
    <div v-else class="task-list-container">
      <table class="task-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>模式</th>
            <th>类型</th>
            <th>状态</th>
            <th>进度</th>
            <th>已处理/总数</th>
            <th>速度</th>
            <th>剩余时间</th>
            <th>发起时间</th>
            <th>结束时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id }}</td>
            <td>{{ getParameter(task.parameters, 'mode') }}</td>
            <td>{{ task.task_type }}</td>
            <td>{{ task.status }}</td>
            <td>
              <div class="progress-bar-container">
                <div
                  class="progress-bar"
                  :style="{ width: (task.percentage || 0) + '%' }"
                ></div>
                <span class="progress-text">{{ (task.percentage || 0).toFixed(1) }}%</span>
              </div>
            </td>
            <td>{{ task.processed_items || 0 }} / {{ task.total_items || 0 }}</td>
            <td>{{ (task.processing_speed || 0).toFixed(2) }} items/s</td>
            <td>{{ formatTime(task.estimated_remaining) }}</td>
            <td>{{ formatDateTime(task.created_at) }}</td>
            <td>{{ formatDateTime(task.completed_at) }}</td>
            <td>
              <button
                @click="onCancel(task.id)"
                :disabled="task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled'"
                class="action-button cancel-button"
              >
                取消
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TaskResponse } from '../services/crawlerApiService'
import { getParameter, formatDateTime, formatTime } from '../utils/taskUtils'

defineProps<{
  tasks: TaskResponse[]
  isLoading: boolean
  error: string | null
  onCancel: (taskId: number) => void
}>()
</script>

<style src="../assets/task.css"></style>
