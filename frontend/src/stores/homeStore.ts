import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BangumiWeekday } from '../services/bangumi/bangumiTypes'

export const useHomeStore = defineStore('home', () => {
  // 基本状态
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 缓存的日历数据
  const cachedCalendar = ref<BangumiWeekday[]>([])
  const hasCalendarData = ref(false)

  // 滚动位置缓存
  const savedScrollPosition = ref(0)

  // 清空缓存数据
  const clearCache = () => {
    cachedCalendar.value = []
    hasCalendarData.value = false
    savedScrollPosition.value = 0
  }

  // 设置日历数据
  const setCalendarData = (data: BangumiWeekday[]) => {
    cachedCalendar.value = data
    hasCalendarData.value = true
  }

  // 保存滚动位置
  const saveScrollPosition = (position: number) => {
    savedScrollPosition.value = position
  }

  // 获取滚动位置
  const getScrollPosition = (): number => {
    return savedScrollPosition.value
  }

  return {
    // 状态
    loading,
    error,

    // 缓存数据
    cachedCalendar,
    hasCalendarData,
    savedScrollPosition,

    // 方法
    clearCache,
    setCalendarData,
    saveScrollPosition,
    getScrollPosition
  }
})
