<template>
  <div class="subscription-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>我的订阅</h1>
      <p v-if="!loading && subscriptions.length > 0">
        共 {{ pagination.total }} 部番剧
      </p>
    </div>

    <!-- 搜索和排序工具栏 -->
    <div class="toolbar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索订阅的番剧..."
          @keyup.enter="handleSearch"
          class="search-input"
        />
        <button @click="handleSearch" class="search-btn">
          🔍
        </button>
      </div>

      <div class="sort-controls">
        <select v-model="sortBy" @change="handleSort" class="sort-select">
          <option value="subscribed_at">订阅时间</option>
          <option value="rating">评分</option>
          <option value="air_date">首播日期</option>
          <option value="name">名称</option>
        </select>

        <button
          @click="toggleSortOrder"
          class="sort-order-btn"
          :class="{ active: sortOrder === 'desc' }"
        >
          {{ sortOrder === 'desc' ? '↓' : '↑' }}
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && subscriptions.length === 0" class="empty-state">
      <div class="empty-icon">📺</div>
      <h3>暂无订阅</h3>
      <p v-if="searchQuery">
        没有找到匹配 "{{ searchQuery }}" 的订阅番剧
      </p>
      <p v-else>
        去<router-link to="/">首页</router-link>发现你喜欢的番剧吧！
      </p>
    </div>

    <!-- 动画卡片网格 -->
    <div v-if="!loading && subscriptions.length > 0" class="anime-grid">
      <AnimeCard
        v-for="subscription in subscriptions"
        :key="subscription.bangumi_id"
        :anime="subscription.anime"
        :show-subscription-button="true"
        @click="goToDetail(subscription.anime)"
      />
    </div>

    <!-- 分页 -->
    <div v-if="!loading && pagination.pages > 1" class="pagination">
      <button
        @click="goToPage(pagination.page - 1)"
        :disabled="pagination.page <= 1"
        class="page-btn"
      >
        上一页
      </button>

      <span class="page-info">
        {{ pagination.page }} / {{ pagination.pages }}
      </span>

      <button
        @click="goToPage(pagination.page + 1)"
        :disabled="pagination.page >= pagination.pages"
        class="page-btn"
      >
        下一页
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSubscriptionStore } from '../stores/subscriptionStore'
import AnimeCard from '../components/AnimeCard.vue'
import type { GetSubscriptionsParams } from '../services/subscription/subscriptionTypes'
import type { BangumiCalendarItem } from '../services/bangumi/bangumiTypes'
import { useRouter } from 'vue-router'

const router = useRouter()
const subscriptionStore = useSubscriptionStore()

// 响应式引用
const searchQuery = ref('')
const sortBy = ref<GetSubscriptionsParams['sort']>('subscribed_at')
const sortOrder = ref<GetSubscriptionsParams['order']>('desc')

// 计算属性
const subscriptions = computed(() => subscriptionStore.subscriptions)
const loading = computed(() => subscriptionStore.loading)
const pagination = computed(() => subscriptionStore.pagination)

// 搜索处理
const handleSearch = () => {
  subscriptionStore.searchSubscriptions(searchQuery.value)
}

// 排序处理
const handleSort = () => {
  subscriptionStore.sortSubscriptions(sortBy.value, sortOrder.value)
}

// 切换排序顺序
const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  handleSort()
}

// 翻页
const goToPage = (page: number) => {
  subscriptionStore.goToPage(page)
}

const goToDetail = (anime: BangumiCalendarItem) => {
  if (anime && anime.id) {
    router.push({ name: 'anime-detail', params: { id: String(anime.id) } })
  }
}

// 页面初始化
onMounted(() => {
  subscriptionStore.fetchSubscriptions()
})
</script>

<style scoped>
.subscription-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 2.5rem;
  color: var(--color-text);
  margin: 0 0 10px 0;
}

.page-header p {
  color: var(--color-text-muted);
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  gap: 20px;
}

.search-box {
  display: flex;
  flex: 1;
  max-width: 400px;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid var(--color-border);
  border-radius: 8px 0 0 8px;
  font-size: 14px;
  outline: none;
}

.search-input:focus {
  border-color: var(--color-primary);
}

.search-btn {
  padding: 10px 15px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  font-size: 16px;
}

.search-btn:hover {
  background: var(--color-primary-dark);
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sort-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.sort-select:focus {
  border-color: var(--color-primary);
}

.sort-order-btn {
  padding: 8px 12px;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.sort-order-btn:hover,
.sort-order-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--color-text-muted);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: var(--color-text);
}

.empty-state p {
  margin-bottom: 5px;
}

.empty-state a {
  color: var(--color-primary);
  text-decoration: none;
}

.empty-state a:hover {
  text-decoration: underline;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
}

.page-btn {
  padding: 10px 20px;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-muted);
  font-size: 14px;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-background-mute);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 15px;
  }

  .search-box {
    max-width: 100%;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
  }

  .pagination {
    gap: 15px;
  }
}
</style>
