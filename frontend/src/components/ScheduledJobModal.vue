<template>
  <div v-if="visible" class="modal-overlay" @click.self="onCancel">
    <transition name="modal-fade">
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
    </transition>
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
<style scoped>
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.25s cubic-bezier(.4,1.3,.6,1), transform 0.25s cubic-bezier(.4,1.3,.6,1);
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
.modal-fade-enter-to, .modal-fade-leave-from {
  opacity: 1;
  transform: scale(1);
}
@media (max-width: 768px) {
  .modal-content {
    width: 100vw !important;
    min-height: 100vh;
    max-width: 100vw !important;
    border-radius: 0 !important;
    left: 0 !important;
    top: 0 !important;
    transform: none !important;
    padding: 2rem 1rem 1.5rem 1rem !important;
    box-shadow: none !important;
    position: fixed !important;
    z-index: 1002;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }
  .modal-overlay {
    align-items: flex-end !important;
    padding: 0 !important;
  }
  .form-actions {
    flex-direction: column;
    gap: 1rem;
  }
  .create-button, .cancel-button {
    font-size: 1.1rem;
    padding: 1rem;
    width: 100%;
    border-radius: 8px;
  }
  h3 {
    font-size: 1.3rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }
  .form-group {
    margin-bottom: 1.25rem;
  }
}
</style>
