<template>
  <div class="home">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="title">IKuYo - 追番助手</h1>
      <p class="subtitle">每日放送</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在加载番剧数据...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadCalendar" class="retry-btn">重试</button>
    </div>

    <!-- 每日放送内容 -->
    <div v-else class="calendar-container">
      <div 
        v-for="day in calendar" 
        :key="day.weekday.id" 
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '../components/AnimeCard.vue'
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
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.title {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.2rem;
  color: #7f8c8d;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
}

.error {
  color: #e74c3c;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-btn:hover {
  background-color: #2980b9;
}

.calendar-container {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.day-section {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.day-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.day-title.today {
  color: #e74c3c;
  border-bottom-color: #e74c3c;
}

.today-badge {
  background: linear-gradient(45deg, #e74c3c, #c0392b);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(231, 76, 60, 0.3);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home {
    padding: 1rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
  }
  
  .day-section {
    padding: 1rem;
  }
}
</style>
