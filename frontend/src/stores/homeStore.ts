import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useHomeStore = defineStore('home', () => {
  // 基本状态
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  return {
    // 状态
    loading,
    error
  }
}) 