<template>
  <div>
    <div v-if="isLoading" class="loading-indicator">加载中...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else-if="!Array.isArray(jobs) || jobs.length === 0" class="no-data-message">暂无定时任务。</div>
    <div v-else class="task-list-container">
      <table class="task-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>Cron表达式</th>
            <th>参数</th>
            <th>启用</th>
            <th>描述</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.job_id">
            <td>{{ job.job_id }}</td>
            <td>{{ job.name }}</td>
            <td>{{ job.cron_expression }}</td>
            <td>{{ job.parameters ? JSON.stringify(job.parameters) : '-' }}</td>
            <td>
              <input
                type="checkbox"
                :checked="job.enabled"
                @change="onToggle(job.job_id)"
              />
            </td>
            <td>{{ job.description || '-' }}</td>
            <td>
              <button @click="onEdit(job)" class="action-button edit-button">编辑</button>
              <button @click="onDelete(job.job_id)" class="action-button delete-button">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
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
</script>

<style src="../assets/task.css"></style>
