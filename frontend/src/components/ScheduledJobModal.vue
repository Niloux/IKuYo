<template>
  <div v-if="visible" class="modal-overlay" @click.self="onCancel">
    <div class="modal-content scale-in">
      <h3>{{ editing ? '编辑' : '创建' }}定时任务</h3>
      <form @submit.prevent="onSubmit">
        <div class="form-group" :class="{ 'has-error': errors.job_id }">
          <label for="jobId">任务ID:</label>
          <input type="text" id="jobId" v-model="job.job_id" :disabled="editing" required />
          <div v-if="errors.job_id" class="error-message">{{ errors.job_id }}</div>
        </div>
        <div class="form-group" :class="{ 'has-error': errors.name }">
          <label for="name">名称:</label>
          <input type="text" id="name" v-model="job.name" required />
          <div v-if="errors.name" class="error-message">{{ errors.name }}</div>
        </div>
        <div class="form-group" :class="{ 'has-error': errors.cron_expression }">
          <label for="cronExpression">Cron表达式:</label>
          <input type="text" id="cronExpression" v-model="job.cron_expression" required />
          <small>例如: 0 0 * * * (每天午夜)</small>
          <div v-if="errors.cron_expression" class="error-message">{{ errors.cron_expression }}</div>
        </div>
        <div class="form-group" :class="{ 'has-error': errors.parameters_json }">
          <label for="parameters">参数 (JSON):</label>
          <textarea id="parameters" v-model="job.parameters_json" rows="5"></textarea>
          <small>例如: {"mode": "homepage", "limit": 10}</small>
          <div v-if="errors.parameters_json" class="error-message">{{ errors.parameters_json }}</div>
        </div>
        <div class="form-group">
          <label for="enabled">
            <input type="checkbox" id="enabled" v-model="job.enabled" />
            启用
          </label>
        </div>
        <div class="form-actions">
          <button type="submit" class="create-button">{{ editing ? '更新' : '创建' }}</button>
          <button type="button" @click="onCancel" class="cancel-button">取消</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ScheduledJobCreate } from '../services/scheduler/schedulerTypes'

defineProps<{
  visible: boolean
  job: ScheduledJobCreate & { parameters_json?: string }
  errors: { [key: string]: string }
  editing: boolean
  onSubmit: () => void
  onCancel: () => void
  onUpdateJob: (job: ScheduledJobCreate & { parameters_json?: string }) => void
}>()
</script>

<style src="../assets/task.css"></style>
