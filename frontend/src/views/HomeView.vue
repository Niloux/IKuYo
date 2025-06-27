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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '../components/AnimeCard.vue'
import WeekNavigation from '../components/WeekNavigation.vue'
import BangumiApiService, { type BangumiWeekday } from '../services/api'

const router = useRouter()

// 响应式数据
const calendar = ref<BangumiWeekday[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

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
const loadCalendar = async () => {
  try {
    loading.value = true
    error.value = null
    
    console.log('开始加载每日放送数据...')
    const data = await BangumiApiService.getCalendar()
    
    // 按照现实周期排序，今天的放在最前面
    calendar.value = sortCalendarByWeek(data)
    
    console.log('数据排序完成，今天是:', new Date().toLocaleDateString('zh-CN', { weekday: 'long' }))
  } catch (err) {
    console.error('加载每日放送失败:', err)
    error.value = '加载失败，请检查网络连接或API服务状态'
  } finally {
    loading.value = false
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
