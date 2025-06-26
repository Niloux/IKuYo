<template>
  <div class="home">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="title">IKuYo - 追番助手</h1>
      <p class="subtitle">今日放送</p>
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
        <h2 class="day-title">{{ day.weekday.cn }}</h2>
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

// 加载每日放送数据
const loadCalendar = async () => {
  try {
    loading.value = true
    error.value = null
    
    console.log('开始加载每日放送数据...')
    const data = await BangumiApiService.getCalendar()
    console.log('API响应数据:', data)
    console.log('数据长度:', data?.length)
    if (data && data.length > 0) {
      console.log('第一天数据:', data[0])
      console.log('第一天番剧数量:', data[0]?.items?.length)
    }
    calendar.value = data
  } catch (err) {
    console.error('加载每日放送失败:', err)
    error.value = '加载失败，请检查网络连接或API服务状态'
  } finally {
    loading.value = false
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
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
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
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  .day-section {
    padding: 1rem;
  }
}
</style>
