<template>
  <div class="home">
    <!-- 直接渲染内容区，无需v-else -->
    <div>
      <!-- 星期导航栏 -->
      <WeekNavigation :calendar="calendar" />
      <!-- 置顶按钮 -->
      <ScrollToTopButton />
      <!-- 每日放送内容 -->
      <div class="calendar-container">
        <!-- 优化：骨架屏加载状态 -->
        <template v-if="shouldShowSkeleton">
          <div v-for="n in 7" :key="`skeleton-${n}`" class="day-section content-card">
            <div class="day-title skeleton-day-title">
              <div class="skeleton-line" style="width: 60px; height: 24px;"></div>
            </div>
            <div class="anime-grid">
              <Skeleton v-for="m in 6" :key="`skeleton-card-${m}`" type="card" />
            </div>
          </div>
        </template>

        <!-- 数据内容 -->
        <template v-else>
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
        </template>
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
import { ref, onMounted, onActivated, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useHomeStore } from '../stores/homeStore'
import { useSubscriptionStore } from '../stores/subscriptionStore'
import AnimeCard from '../components/AnimeCard.vue'
import WeekNavigation from '../components/WeekNavigation.vue'
import ScrollToTopButton from '../components/ScrollToTopButton.vue'
import Skeleton from '../components/common/Skeleton.vue'
import BangumiApiService from '../services/bangumi/bangumiApiService'
import type { BangumiWeekday } from '../services/bangumi/bangumiTypes'
import { ensureScrollToTop } from '../utils/scrollUtils'
import { onBeforeRouteLeave } from 'vue-router'

const route = useRoute()
const router = useRouter()
const homeStore = useHomeStore()
const subscriptionStore = useSubscriptionStore()

// 从store获取响应式状态
const { loading, error, cachedCalendar, hasCalendarData } = storeToRefs(homeStore)

// 优化：计算属性，只有在真正需要加载且无数据时才显示骨架屏
const shouldShowSkeleton = computed(() => {
  return loading.value && !hasCalendarData.value
})

// 缓存今天的weekdayId，避免重复计算
const todayWeekdayId = computed(() => {
  const today = new Date().getDay()
  return today === 0 ? 7 : today
})

// 优化：判断是否是今天
const isToday = (weekdayId: number): boolean => {
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId
  return adjustedWeekdayId === todayWeekdayId.value
}

// 优化：获取距离今天的天数差
const getDaysFromToday = (weekdayId: number): number => {
  const adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId
  let diff = adjustedWeekdayId - todayWeekdayId.value
  if (diff < 0) {
    diff += 7
  }
  return diff
}

// 优化：使用computed自动排序日历数据，避免重复计算
const calendar = computed(() => {
  if (!cachedCalendar.value.length) return []

  return [...cachedCalendar.value].sort((a, b) => {
    if (isToday(a.weekday.id)) return -1
    if (isToday(b.weekday.id)) return 1
    return getDaysFromToday(a.weekday.id) - getDaysFromToday(b.weekday.id)
  })
})

// 优化：简化加载逻辑，避免状态冲突
const loadCalendar = async () => {
  try {
    homeStore.loading = true
    homeStore.error = null

    const data = await BangumiApiService.getCalendar()
    // 直接存储原始数据，排序由computed处理
    homeStore.setCalendarData(data)
  } catch (err) {
    console.error('加载每日放送失败:', err)
    homeStore.error = '加载失败，请检查网络连接或API服务状态'
  } finally {
    homeStore.loading = false
  }
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
  // 拉取全部订阅ID，确保首页订阅状态准确
  subscriptionStore.fetchAllSubscriptionIds()
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
}

/* 优化：骨架屏样式 */
.skeleton-day-title {
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.skeleton-line {
  background: #e0e0e0;
  border-radius: 4px;
  animation: skeleton-loading 1.2s infinite linear;
  background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
  background-size: 200% 100%;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
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
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem;
  }
  .day-section {
    padding: 1rem 0.5rem;
    border-radius: 8px;
    margin-bottom: 1.2rem;
  }
  .day-title {
    font-size: 1.1rem;
    margin-bottom: 1rem;
    padding-bottom: 0.25rem;
    gap: 0.5rem;
  }
  .today-badge {
    font-size: 0.7rem;
    padding: 0.18rem 0.4rem;
    border-radius: 8px;
  }
}
</style>
