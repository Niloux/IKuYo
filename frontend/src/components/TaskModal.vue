<template>
  <div v-if="visible" class="modal-overlay" @click.self="onCancel">
    <div class="modal-content">
      <h3>创建新爬虫任务</h3>
      <form @submit.prevent="onSubmit">
        <div class="form-group" :class="{ 'has-error': errors.mode }">
          <label for="mode">模式:</label>
          <select id="mode" v-model="task.mode" required>
            <option value="">请选择模式</option>
            <option value="homepage">首页</option>
            <option value="bangumi_id">番剧ID</option>
            <option value="url">URL</option>
          </select>
          <div v-if="errors.mode" class="error-message">{{ errors.mode }}</div>
        </div>

        <div class="form-group" v-if="task.mode === 'bangumi_id'" :class="{ 'has-error': errors.bangumi_id }">
          <label for="bangumiId">番剧ID:</label>
          <input type="number" id="bangumiId" v-model.number="task.bangumi_id" />
          <div v-if="errors.bangumi_id" class="error-message">{{ errors.bangumi_id }}</div>
        </div>

        <div class="form-group" v-if="task.mode === 'url'" :class="{ 'has-error': errors.start_url }">
          <label for="startUrl">起始URL:</label>
          <input type="text" id="startUrl" v-model="task.start_url" />
          <div v-if="errors.start_url" class="error-message">{{ errors.start_url }}</div>
        </div>

        <div class="form-group" :class="{ 'has-error': errors.limit }">
          <label for="limit">限制数量 (可选):</label>
          <input type="number" id="limit" v-model.number="task.limit" />
          <div v-if="errors.limit" class="error-message">{{ errors.limit }}</div>
        </div>

        <div class="form-actions">
          <button type="submit" class="create-button">创建</button>
          <button type="button" @click="onCancel" class="cancel-button">取消</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, toRefs, watch } from 'vue'
import type { CrawlerTaskCreate } from '../services/crawlerApiService'

defineProps<{
  visible: boolean
  task: CrawlerTaskCreate & { bangumi_id?: number }
  errors: { [key: string]: string }
  onSubmit: () => void
  onCancel: () => void
  onUpdateTask: (task: CrawlerTaskCreate & { bangumi_id?: number }) => void
}>()
</script>

<style src="../assets/task.css"></style>
