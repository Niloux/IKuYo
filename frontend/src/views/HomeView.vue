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
          class="day-section"
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
              :should-load-image="isFirstBatch(dayIndex, animeIndex) || secondBatchEnabled"
              @click="goToDetail(anime.id)"
              @image-load="onImageLoad"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useHomeStore } from '../stores/homeStore'
import AnimeCard from '../components/AnimeCard.vue'
import WeekNavigation from '../components/WeekNavigation.vue'
import ScrollToTopButton from '../components/ScrollToTopButton.vue'
import BangumiApiService, { type BangumiWeekday } from '../services/api'

const router = useRouter()
const homeStore = useHomeStore()

// 从store获取响应式状态
const { loading, error } = storeToRefs(homeStore)

// 响应式数据
const calendar = ref<BangumiWeekday[]>([])

// 分批加载状态
const firstBatchLoaded = ref(0)
const secondBatchEnabled = ref(false)
let totalFirstBatch = 0

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
    
    console.log('开始加载每日放送数据...')
    const data = await BangumiApiService.getCalendar()
    
    // 按照现实周期排序，今天的放在最前面
    calendar.value = sortCalendarByWeek(data)
    
    // 计算第一批加载的总数（一半）
    totalFirstBatch = Math.ceil(
      calendar.value.reduce((total, day) => total + day.items.length, 0) / 2
    )
    
    console.log('数据排序完成，今天是:', new Date().toLocaleDateString('zh-CN', { weekday: 'long' }))
    console.log(`第一批需要加载 ${totalFirstBatch} 张图片`)
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

// 判断是否应该在第一批加载
const isFirstBatch = (dayIndex: number, animeIndex: number): boolean => {
  let currentIndex = 0
  for (let i = 0; i < dayIndex; i++) {
    currentIndex += calendar.value[i].items.length
  }
  currentIndex += animeIndex
  return currentIndex < totalFirstBatch
}

// 图片加载完成处理
const onImageLoad = () => {
  firstBatchLoaded.value++
  if (firstBatchLoaded.value >= totalFirstBatch) {
    console.log('第一批加载完成，开始加载第二批')
    secondBatchEnabled.value = true
  }
}

// 跳转到番剧详情页
const goToDetail = (bangumiId: number) => {
  router.push(`/anime/${bangumiId}`)
}

// 组件挂载时加载数据
onMounted(() => {
  loadCalendar()
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
