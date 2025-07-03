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
            <option value="season">季度</option>
            <option value="year">年份</option>
          </select>
          <div v-if="errors.mode" class="error-message">{{ errors.mode }}</div>
        </div>

        <div class="form-group" v-if="task.mode === 'season' || task.mode === 'year'" :class="{ 'has-error': errors.year }">
          <label for="year">年份:</label>
          <select id="year" v-model.number="task.year" required>
            <option value="">请选择年份</option>
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
          </select>
          <div v-if="errors.year" class="error-message">{{ errors.year }}</div>
        </div>

        <div class="form-group" v-if="task.mode === 'season'" :class="{ 'has-error': errors.season }">
          <label for="season">季度:</label>
          <select id="season" v-model="task.season" required>
            <option value="">请选择季度</option>
            <option value="春">春</option>
            <option value="夏">夏</option>
            <option value="秋">秋</option>
            <option value="冬">冬</option>
          </select>
          <div v-if="errors.season" class="error-message">{{ errors.season }}</div>
        </div>

        <div class="form-group" :class="{ 'has-error': errors.limit }">
          <label for="limit">限制数量 (可选):</label>
          <input type="number" id="limit" v-model.number="task.limit" min="1" />
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
import { computed } from 'vue'
import type { CrawlerTaskCreate } from '../services/crawlerApiService'

defineProps<{
  visible: boolean
  task: CrawlerTaskCreate
  errors: { [key: string]: string }
  onSubmit: () => void
  onCancel: () => void
  onUpdateTask: (task: CrawlerTaskCreate) => void
}>()

// 计算可用年份（从2013年到当前年份）
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let year = currentYear; year >= 2013; year--) {
    years.push(year)
  }
  return years
})
</script>

<style src="../assets/task.css"></style>
