import { defineStore } from 'pinia'
import { ref } from 'vue'
import { debounce } from '../utils/debounce'
import type { BangumiWeekday } from '../services/api'

const STORAGE_KEY = 'ikuyo_home_state'

export const useHomeStore = defineStore('home', () => {
  // 状态数据
  const scrollPosition = ref(0)
  const calendarData = ref<BangumiWeekday[]>([])
  const lastLoadTime = ref<number>(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 保存滚动位置
  const saveScrollPosition = (position: number) => {
    scrollPosition.value = position
    saveToStorage()
    console.log(`保存首页滚动位置: ${position}`)
  }
  
  // 恢复滚动位置
  const restoreScrollPosition = (): number => {
    console.log(`恢复首页滚动位置: ${scrollPosition.value}`)
    return scrollPosition.value
  }
  
  // 缓存日历数据
  const cacheCalendarData = (data: BangumiWeekday[]) => {
    calendarData.value = data
    lastLoadTime.value = Date.now()
    saveToStorage()
    console.log(`缓存首页日历数据，共${data.length}天`)
  }
  
  // 检查缓存是否有效（5分钟内）
  const isCacheValid = (): boolean => {
    const CACHE_DURATION = 5 * 60 * 1000 // 5分钟
    const isValid = calendarData.value.length > 0 && (Date.now() - lastLoadTime.value < CACHE_DURATION)
    console.log(`检查首页缓存有效性: ${isValid}`)
    return isValid
  }
  
  // 获取缓存的日历数据
  const getCachedCalendarData = (): BangumiWeekday[] => {
    return calendarData.value
  }
  
  // 清空状态（用于重新进入首页）
  const clearState = () => {
    scrollPosition.value = 0
    calendarData.value = []
    lastLoadTime.value = 0
    loading.value = false
    error.value = null
    clearStorage()
    console.log('清空首页状态')
  }
  
  // 防抖保存状态到sessionStorage
  const saveToStorage = debounce(() => {
    try {
      const state = {
        scrollPosition: scrollPosition.value,
        calendarData: calendarData.value,
        lastLoadTime: lastLoadTime.value,
        timestamp: Date.now()
      }
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      console.log('首页状态已防抖保存到sessionStorage')
    } catch (err) {
      console.error('保存首页状态失败:', err)
    }
  }, 300)
  
  // 从sessionStorage恢复状态
  const restoreFromStorage = () => {
    try {
      const saved = window.sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const state = JSON.parse(saved)
        scrollPosition.value = state.scrollPosition || 0
        calendarData.value = state.calendarData || []
        lastLoadTime.value = state.lastLoadTime || 0
        console.log('从sessionStorage恢复首页状态')
      }
    } catch (err) {
      console.error('恢复首页状态失败:', err)
    }
  }
  
  // 清除sessionStorage
  const clearStorage = () => {
    try {
      window.sessionStorage.removeItem(STORAGE_KEY)
    } catch (err) {
      console.error('清除首页sessionStorage失败:', err)
    }
  }
  
  return {
    // 状态
    scrollPosition,
    calendarData,
    lastLoadTime,
    loading,
    error,
    
    // 方法
    saveScrollPosition,
    restoreScrollPosition,
    cacheCalendarData,
    isCacheValid,
    getCachedCalendarData,
    clearState,
    restoreFromStorage
  }
}) 