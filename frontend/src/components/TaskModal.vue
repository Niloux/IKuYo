<template>
  <div v-if="visible" class="modal-overlay" @click.self="onCancel">
    <transition name="modal-fade">
      <div class="modal-content scale-in">
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
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CrawlerTaskCreate } from '../services/crawler/crawlerTypes'

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

/* 移动端全屏/底部弹出适配 */
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
