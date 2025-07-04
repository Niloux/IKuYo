<template>
  <div class="home">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在加载番剧数据...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadCalendar" class="retry-btn">重试</button>
    </div>

    <!-- 内容区域 -->
    <div v-else>
      <!-- 星期导航栏 -->
      <WeekNavigation :calendar="calendar" />

      <!-- 置顶按钮 -->
      <ScrollToTopButton />

      <!-- 每日放送内容 -->
      <div class="calendar-container">
        <div
          v-for="(day, dayIndex) in calendar"
          :key="day.weekday.id"
          :id="`day-${day.weekday.id}`"
          class="day-section content-card"
        >
          <h2 class="day-title" :class="{ 'today': isToday(day.weekday.id) }">
            {{ day.weekday.cn }}
            <span v-if="isToday(day.weekday.id)" class="today-badge">今天</span>
          </h2>
          <div class="anime-grid">
            <AnimeCard
              v-for="(anime, animeIndex) in day.items"
              :key="anime.id"
              :anime="anime"
              @click="goToDetail(anime.id)"
              @image-load="() => {}"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'HomeView'
}
</script>

<script setup lang="ts">
import { ref, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useHomeStore } from '../stores/homeStore'
import AnimeCard from '../components/AnimeCard.vue'
import WeekNavigation from '../components/WeekNavigation.vue'
import ScrollToTopButton from '../components/ScrollToTopButton.vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { BangumiWeekday } from '../services/bangumi/bangumiTypes'
import { ensureScrollToTop } from '../utils/scrollUtils'
import { onBeforeRouteLeave } from 'vue-router'

const route = useRoute()
const router = useRouter()
const homeStore = useHomeStore()

// 从store获取响应式状态
const { loading, error, cachedCalendar, hasCalendarData } = storeToRefs(homeStore)

// 响应式数据 - 现在使用store中的缓存数据
const calendar = cachedCalendar

// 获取距离今天的天数差
const getDaysFromToday = (weekdayId: number): number => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId

  let diff = adjustedWeekdayId - todayId
  if (diff < 0) {
    diff += 7
  }
  return diff
}

// 按照现实周期排序日历数据
const sortCalendarByWeek = (data: BangumiWeekday[]): BangumiWeekday[] => {
  return [...data].sort((a, b) => {
    if (isToday(a.weekday.id)) return -1
    if (isToday(b.weekday.id)) return 1

    return getDaysFromToday(a.weekday.id) - getDaysFromToday(b.weekday.id)
  })
}

// 加载每日放送数据
const loadCalendar = async () => {
  try {
    homeStore.loading = true
    homeStore.error = null

    const data = await BangumiApiService.getCalendar()

    // 按照现实周期排序，今天的放在最前面
    const sortedData = sortCalendarByWeek(data)
    homeStore.setCalendarData(sortedData)
  } catch (err) {
    console.error('加载每日放送失败:', err)
    homeStore.error = '加载失败，请检查网络连接或API服务状态'
  } finally {
    homeStore.loading = false
  }
}

// 判断是否是今天
const isToday = (weekdayId: number): boolean => {
  const today = new Date().getDay()
  const todayId = today === 0 ? 7 : today
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId
  return adjustedWeekdayId === todayId
}

// 跳转到番剧详情页
const goToDetail = (bangumiId: number) => {
  router.push(`/anime/${bangumiId}`)
}

// 路由守卫：离开页面时保存滚动位置
onBeforeRouteLeave((to, from) => {
  const currentScrollPosition = window.pageYOffset || document.documentElement.scrollTop
  homeStore.saveScrollPosition(currentScrollPosition)

  // 如果是去往详情页，设置sessionStorage标记
  if (to.name === 'anime-detail' || to.name === 'library-detail') {
    sessionStorage.setItem('fromDetail', 'true')
  } else {
    // 去往其他页面，清除标记
    sessionStorage.removeItem('fromDetail')
  }
})

// keep-alive组件恢复时的处理
onActivated(() => {
  const fromDetail = sessionStorage.getItem('fromDetail')

  if (fromDetail === 'true') {
    // 从详情页返回，立即恢复滚动位置
    sessionStorage.removeItem('fromDetail')
    const savedPosition = homeStore.getScrollPosition()
    window.scrollTo({ top: savedPosition, behavior: 'instant' })
  } else {
    // 从其他页面返回，滚动到顶部
    ensureScrollToTop()
  }
})

// 组件挂载时加载数据
onMounted(() => {
  // 首次挂载时加载数据，滚动位置管理由keep-alive + onActivated处理
  if (!hasCalendarData.value) {
    loadCalendar()
  }
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
  /* 移除通用卡片样式，改为复用.content-card */
  /* background: var(--color-bg-white); */
  /* border-radius: var(--radius-md); */
  /* padding: 2rem; */
  /* box-shadow: var(--shadow-md); */
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
