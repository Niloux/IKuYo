<template>
  <div class="home">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在加载番剧数据...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="() => loadCalendar(true)" class="retry-btn">重试</button>
    </div>

    <!-- 内容区域 -->
    <div v-else>
      <!-- 星期导航栏 -->
      <WeekNavigation :calendar="calendar" />

      <!-- 每日放送内容 -->
      <div class="calendar-container">
        <div 
          v-for="day in calendar" 
          :key="day.weekday.id" 
          :id="`day-${day.weekday.id}`"
          class="day-section"
        >
          <h2 class="day-title" :class="{ 'today': isToday(day.weekday.id) }">
            {{ day.weekday.cn }}
            <span v-if="isToday(day.weekday.id)" class="today-badge">今天</span>
          </h2>
          <div class="anime-grid">
            <AnimeCard
              v-for="anime in day.items"
              :key="anime.id"
              :anime="anime"
              @click="goToDetail(anime.id)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useHomeStore } from '../stores/homeStore'
import { useNavigationStore } from '../stores/navigationStore'
import { ensureScrollToTop, restoreScrollPosition as restoreScroll, getCurrentScrollPosition } from '../utils/scrollUtils'
import AnimeCard from '../components/AnimeCard.vue'
import WeekNavigation from '../components/WeekNavigation.vue'
import BangumiApiService, { type BangumiWeekday } from '../services/api'

const router = useRouter()
const homeStore = useHomeStore()
const navigationStore = useNavigationStore()

// 从store获取响应式状态
const { loading, error } = storeToRefs(homeStore)

// 本地状态
const calendar = ref<BangumiWeekday[]>([])

// 按照现实周期排序每日放送
const sortCalendarByWeek = (data: BangumiWeekday[]): BangumiWeekday[] => {
  // 获取今天是星期几 (0=星期日, 1=星期一, ..., 6=星期六)
  const today = new Date().getDay()
  
  // 将星期日从0调整为7，这样更容易计算
  const todayId = today === 0 ? 7 : today
  
  // 按照今天开始的顺序排序
  return data.sort((a, b) => {
    // 计算距离今天的天数
    const getDaysFromToday = (weekdayId: number) => {
      const adjustedId = weekdayId === 0 ? 7 : weekdayId
      const diff = adjustedId - todayId
      return diff >= 0 ? diff : diff + 7
    }
    
    return getDaysFromToday(a.weekday.id) - getDaysFromToday(b.weekday.id)
  })
}

// 加载每日放送数据
const loadCalendar = async (forceReload = false) => {
  try {
    homeStore.loading = true
    homeStore.error = null
    
    // 检查是否可以使用缓存
    if (!forceReload && homeStore.isCacheValid()) {
      console.log('使用缓存的首页日历数据')
      calendar.value = sortCalendarByWeek(homeStore.getCachedCalendarData())
      homeStore.loading = false
      return
    }
    
    console.log('开始加载每日放送数据...')
    const data = await BangumiApiService.getCalendar()
    
    // 按照现实周期排序，今天的放在最前面
    calendar.value = sortCalendarByWeek(data)
    
    // 缓存数据到store
    homeStore.cacheCalendarData(data)
    
    console.log('数据排序完成，今天是:', new Date().toLocaleDateString('zh-CN', { weekday: 'long' }))
  } catch (err) {
    console.error('加载每日放送失败:', err)
    homeStore.error = '加载失败，请检查网络连接或API服务状态'
  } finally {
    homeStore.loading = false
    
    // 如果是强制重新加载（初始状态），确保滚动到顶部
    if (forceReload) {
      nextTick(() => {
        if (window.scrollY > 0) {
          window.scrollTo({ top: 0, behavior: 'instant' })
          console.log('数据加载完成，确保滚动到顶部')
        }
      })
    }
  }
}

// 判断是否是今天
const isToday = (weekdayId: number): boolean => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId
  return adjustedWeekdayId === todayId
}

// 保存滚动位置（优化版）
const saveScrollPosition = () => {
  const scrollY = getCurrentScrollPosition()
  homeStore.saveScrollPosition(scrollY)
}

// 跳转到番剧详情页
const goToDetail = (bangumiId: number) => {
  saveScrollPosition()
  // 记录即将访问的详情页路径，用于返回时检测
  navigationStore.recordDetailPageVisit(`/anime/${bangumiId}`, '/')
  router.push(`/anime/${bangumiId}`)
}

// 初始化首页状态（优化版）
const initializeHomeState = () => {
  // 手动恢复存储状态
  homeStore.restoreFromStorage()
  
  const isReturning = navigationStore.isReturningFromDetail('/')
  
  if (isReturning) {
    console.log('从详情页返回首页，恢复状态')
    loadCalendar(false) // 使用缓存数据
    // 恢复滚动位置
    const position = homeStore.restoreScrollPosition()
    restoreScroll(position)
  } else {
    console.log('重新进入首页，清空状态')
    homeStore.clearState()
    ensureScrollToTop() // 统一的滚动重置
    loadCalendar(true) // 强制重新加载
  }
}

// 组件挂载时初始化状态
onMounted(() => {
  initializeHomeState()
})

// 组件卸载前保存滚动位置
onBeforeUnmount(() => {
  saveScrollPosition()
})
</script>

<style scoped>
.home {
  padding: 0; /* 移除内边距，因为AppLayout已经处理了 */
}



.loading, .error {
  text-align: center;
  padding: 3rem;
}

.error {
  color: var(--color-error);
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
  font-weight: 500;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.calendar-container {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.day-section {
  background: var(--color-bg-white);
  border-radius: var(--radius-md);
  padding: 2rem;
  box-shadow: var(--shadow-md);
  transition: transform var(--transition-normal);
}

.day-section:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.day-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-dark);
  margin-bottom: 1.5rem;
  border-bottom: 2px solid var(--color-primary);
  padding-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.day-title.today {
  color: var(--color-error);
  border-bottom-color: var(--color-error);
}

.today-badge {
  background: linear-gradient(135deg, var(--color-error), #dc2626);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-lg);
  font-size: 0.75rem;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
  }
  
  .day-section {
    padding: 1.5rem;
  }
}
</style>
