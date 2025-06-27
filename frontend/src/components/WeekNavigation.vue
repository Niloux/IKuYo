<template>
  <div class="floating-nav" ref="floatingNavRef">
    <!-- 展开面板 -->
    <transition name="nav-panel">
      <div v-show="isExpanded" class="nav-panel">
                  <div 
            v-for="day in sortedDays" 
            :key="day.weekday.id"
            class="nav-card"
            :class="{ 
              'today': isToday(day.weekday.id),
              'active': activeWeekdayId === day.weekday.id
            }"
            :style="{ 
              background: getWeekdayGradient(day.weekday.id) 
            }"
            @click="handleCardClick(day.weekday.id)"
          >
            <div class="card-day">{{ getWeekdayAbbr(day.weekday.en) }}</div>
          </div>
      </div>
    </transition>
    
    <!-- 浮动按钮 -->
    <button 
      class="nav-toggle" 
      @click="toggleNav" 
      :class="{ 'expanded': isExpanded }"
      :style="{ 
        background: getTodayGradient() 
      }"
    >
      <div class="toggle-content">
        <div class="toggle-text">{{ getTodayShort() }}</div>
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { BangumiWeekday } from '../services/api'

// Props定义
const props = defineProps<{
  calendar: BangumiWeekday[]
}>()

// 当前激活的星期
const activeWeekdayId = ref<number | null>(null)

// 展开状态
const isExpanded = ref(false)

// 浮动导航引用
const floatingNavRef = ref<HTMLElement | null>(null)

// 按照星期顺序排序（周一到周日）
const sortedDays = computed(() => {
  return [...props.calendar].sort((a, b) => {
    const getWeekOrder = (weekdayId: number) => {
      // 将星期日(7)调整为最后一个位置
      return weekdayId === 7 ? 7 : weekdayId
    }
    return getWeekOrder(a.weekday.id) - getWeekOrder(b.weekday.id)
  })
})



// 判断是否是今天
const isToday = (weekdayId: number): boolean => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId
  return adjustedWeekdayId === todayId
}

// 获取英文缩写
const getWeekdayAbbr = (englishName: string): string => {
  const abbrMap: Record<string, string> = {
    'Monday': 'Mon',
    'Tuesday': 'Tue', 
    'Wednesday': 'Wed',
    'Thursday': 'Thu',
    'Friday': 'Fri',
    'Saturday': 'Sat',
    'Sunday': 'Sun'
  }
  return abbrMap[englishName] || englishName.slice(0, 3)
}

// 获取星期的渐变色彩
const getWeekdayGradient = (weekdayId: number): string => {
  const gradientMap: Record<number, string> = {
    // 自然过渡：蓝色 → 紫色 → 粉色 → 橙色 → 绿色
    1: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',     // Monday 蓝色
    2: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',     // Tuesday 蓝紫色
    3: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',     // Wednesday 紫色
    4: 'linear-gradient(135deg, #a855f7 0%, #d946ef 100%)',     // Thursday 紫粉色
    5: 'linear-gradient(135deg, #d946ef 0%, #f97316 100%)',     // Friday 粉橙色
    
    // 周末：暖色调过渡到绿色
    6: 'linear-gradient(135deg, #f97316 0%, #10b981 100%)',     // Saturday 橙绿色
    7: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',     // Sunday 绿色
    0: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'      // Sunday (backup for 0)
  }
  
  return gradientMap[weekdayId] || 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)'
}

// 获取今天的英文全称
const getTodayShort = (): string => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  const todayWeekday = props.calendar.find(day => {
    const adjustedId = day.weekday.id === 0 ? 7 : day.weekday.id
    return adjustedId === todayId
  })
  return todayWeekday ? todayWeekday.weekday.en : 'Today'
}

// 获取今天对应的渐变色
const getTodayGradient = (): string => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  return getWeekdayGradient(todayId)
}

// 切换展开状态
const toggleNav = () => {
  isExpanded.value = !isExpanded.value
}

// 处理卡片点击
const handleCardClick = (weekdayId: number) => {
  scrollToSection(weekdayId)
  isExpanded.value = false // 点击后自动收起
}

// 滚动到指定星期区域
const scrollToSection = (weekdayId: number) => {
  const targetElement = document.getElementById(`day-${weekdayId}`)
  if (targetElement) {
    const headerHeight = 70 // AppHeader高度
    const offset = 30 // 额外缓冲
    const elementPosition = targetElement.offsetTop - headerHeight - offset
    
    window.scrollTo({
      top: elementPosition,
      behavior: 'smooth'
    })
  }
}

// 点击外部区域关闭导航
const handleClickOutside = (event: Event) => {
  if (floatingNavRef.value && !floatingNavRef.value.contains(event.target as Node)) {
    isExpanded.value = false
  }
}

// Intersection Observer 用于检测当前可见的星期区域
let observer: IntersectionObserver | null = null

const setupIntersectionObserver = () => {
  if (typeof window === 'undefined') return

  const options = {
    root: null,
    rootMargin: '-100px 0px -60% 0px', // 顶部留100px，底部留60%空间
    threshold: 0.3
  }

  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const weekdayId = parseInt(entry.target.id.replace('day-', ''))
        activeWeekdayId.value = weekdayId
      }
    })
  }, options)

  // 观察所有星期区域
  props.calendar.forEach((day) => {
    const element = document.getElementById(`day-${day.weekday.id}`)
    if (element) {
      observer?.observe(element)
    }
  })
}

const cleanupObserver = () => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

// 组件挂载时设置观察器
onMounted(() => {
  // 延迟设置观察器，确保DOM元素已渲染
  setTimeout(setupIntersectionObserver, 100)
  // 添加点击外部区域监听
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时清理观察器
onUnmounted(() => {
  cleanupObserver()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.floating-nav {
  position: fixed;
  bottom: 30px;
  right: 60px;
  z-index: 1000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.nav-panel {
  position: absolute;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(20px) saturate(180%);
  border-radius: 30px;
  padding: 16px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 6px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  min-width: 100px;
}

.nav-card {
  color: white;
  border-radius: 20px;
  padding: 10px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.08);
  margin-bottom: 8px;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.nav-card:last-child {
  margin-bottom: 0;
}

.nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.2) 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    rgba(255, 255, 255, 0.05) 100%);
  pointer-events: none;
  transition: opacity 0.3s ease;
  opacity: 0;
}

.nav-card:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-card:hover::before {
  opacity: 1;
}

.nav-card.active {
  transform: translateY(-1px) scale(1.05);
  box-shadow: 
    0 8px 25px rgba(255, 215, 0, 0.3),
    0 2px 8px rgba(255, 215, 0, 0.2);
}

.nav-card.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255, 215, 0, 0.3) 0%, 
    rgba(255, 215, 0, 0.1) 100%);
  pointer-events: none;
}

.card-day {
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
}

.nav-toggle {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  outline: none;
  cursor: pointer;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  backdrop-filter: blur(10px);
}

.nav-toggle::before {
  content: '';
  position: absolute;
  top: 1px;
  left: 1px;
  right: 1px;
  bottom: 1px;
  border-radius: 50%;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.05) 50%,
    rgba(0, 0, 0, 0.05) 100%);
  pointer-events: none;
}

.nav-toggle:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 
    0 12px 48px rgba(0, 0, 0, 0.2),
    0 4px 16px rgba(0, 0, 0, 0.15);
}

.nav-toggle.expanded {
  background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
  box-shadow: 
    0 8px 32px rgba(255, 107, 107, 0.4),
    0 2px 8px rgba(255, 107, 107, 0.2);
  transform: scale(1.1);
}

.toggle-content {
  color: white;
  text-align: center;
  font-weight: 600;
  position: relative;
  z-index: 1;
}

.toggle-text {
  font-size: 0.625rem;
  opacity: 0.95;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 展开/收起动画 */
.nav-panel-enter-active,
.nav-panel-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  transform-origin: bottom center;
}

.nav-panel-enter-from,
.nav-panel-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px) scale(0.8);
  backdrop-filter: blur(0px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .floating-nav {
    bottom: 20px;
    right: 30px;
  }
  
  .nav-toggle {
    width: 48px;
    height: 48px;
  }
  
  .nav-panel {
    bottom: 65px;
    min-width: 90px;
    padding: 12px;
    border-radius: 24px;
  }
  
  .nav-card {
    padding: 8px 12px;
    min-height: 32px;
    margin-bottom: 6px;
          border-radius: 18px;
  }
  
  .card-day {
    font-size: 0.75rem;
  }
  
  .toggle-text {
    font-size: 0.5rem;
  }
}

@media (max-width: 480px) {
  .nav-panel {
    min-width: 80px;
    padding: 10px;
  }
  
  .nav-card {
    padding: 6px 10px;
    min-height: 28px;
  }
}
</style> 