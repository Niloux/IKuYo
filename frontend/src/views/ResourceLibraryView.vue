<template>
  <div class="resource-library">
    <div class="content-card">
      <div class="search-section">
        <div class="search-container">
          <div class="search-box">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索番剧名称..."
              class="search-input"
              @input="handleSearchInput"
            />
          </div>
        </div>
      </div>
      <div class="results-section">
        <Skeleton :loading="loading" type="list" :rows="8" customClass="library-skeleton" />
        <div v-if="!loading && searchResults.length > 0">
          <div class="results-header">
            <h2>搜索结果</h2>
            <span class="results-count">
              找到 {{ pagination.total }} 个结果
            </span>
          </div>
          <div class="anime-grid">
            <AnimeCard
              v-for="anime in searchResults"
              :key="anime.id"
              :anime="anime"
              @click="goToLibraryDetail(anime.id)"
            />
          </div>
          <div v-if="pagination.total_pages > 1" class="pagination">
            <button
              @click="searchStore.goToPage(pagination.current_page - 1)"
              :disabled="!pagination.has_prev"
              class="pagination-btn"
            >
              上一页
            </button>
            <div class="page-numbers">
              <span
                v-for="page in searchStore.getVisiblePages()"
                :key="page"
                :class="['page-number', { active: page === pagination.current_page }]"
                @click="searchStore.goToPage(page)"
              >
                {{ page }}
              </span>
            </div>
            <button
              @click="searchStore.goToPage(pagination.current_page + 1)"
              :disabled="!pagination.has_next"
              class="pagination-btn"
            >
              下一页
            </button>
          </div>
        </div>
        <div v-else-if="!loading && hasSearched && searchResults.length === 0" class="empty-results">
          <p>没有找到相关番剧</p>
          <p class="empty-subtitle">尝试使用其他关键词搜索</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'ResourceLibraryView'
}
</script>

<script setup lang="ts">
import { ref, onMounted, onActivated, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { defineAsyncComponent } from 'vue'
import { useSearchStore } from '../stores/searchStore'
import { ensureScrollToTop, getCurrentScrollPosition, restoreScrollPosition } from '../utils/scrollUtils'
import { onBeforeRouteLeave } from 'vue-router'
import Skeleton from '../components/common/Skeleton.vue'

const route = useRoute()
const router = useRouter()
const searchStore = useSearchStore()

// 从store获取响应式状态
const {
  searchQuery,
  searchResults,
  loading,
  error,
  hasSearched,
  pagination
} = storeToRefs(searchStore)

// 测试keep-alive是否工作的计数器
const mountCounter = ref(0)

// 防抖处理
let searchTimeout: number | null = null

// 保存滚动位置的key
const SCROLL_KEY = 'library_scroll_position'

const AnimeCard = defineAsyncComponent(() => import('../components/AnimeCard.vue'))

const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    if (searchQuery.value.trim()) {
      searchStore.performSearch(1, { debounce: true, delay: 300 })
    } else {
      // 如果搜索框为空，清空结果
      searchStore.clearSearchState()
    }
  }, 150) as unknown as number
}

// 重试搜索的包装函数
const retrySearch = () => {
  searchStore.performSearch()
}

// 跳转到资源库详情页
const goToLibraryDetail = (bangumiId: number) => {
  // 保存滚动位置
  const currentScroll = getCurrentScrollPosition()
  sessionStorage.setItem(SCROLL_KEY, String(currentScroll))
  router.push(`/library/detail/${bangumiId}`)
}

// keep-alive组件恢复时的处理
onActivated(() => {
  const fromDetail = sessionStorage.getItem('fromDetail')
  if (fromDetail === 'true') {
    // 从详情页返回，恢复滚动位置
    sessionStorage.removeItem('fromDetail')
    const savedScroll = Number(sessionStorage.getItem(SCROLL_KEY) || 0)
    nextTick(() => {
      restoreScrollPosition(savedScroll)
    })
  } else {
    // 其他情况清空状态并滚动到顶部
    searchStore.clearSearchState()
    nextTick(() => {
      ensureScrollToTop()
    })
  }
})

// 组件挂载时清空搜索状态，确保每次都是干净的初始状态
onMounted(() => {
  mountCounter.value++

  // 检查是否从详情页返回（第一次缓存时也需要检查）
  const fromDetail = sessionStorage.getItem('fromDetail')

  if (fromDetail === 'true') {
    // 从详情页返回，保持搜索状态，不清空
    sessionStorage.removeItem('fromDetail') // 清除标记
  } else {
    // 首次进入或刷新，清空搜索状态
    searchStore.clearSearchState()
  }
})

onBeforeRouteLeave((to: any, from: any) => {
  // 离开去详情页时保存滚动位置
  if (to.name === 'library-detail') {
    const currentScroll = getCurrentScrollPosition()
    sessionStorage.setItem(SCROLL_KEY, String(currentScroll))
    sessionStorage.setItem('fromDetail', 'true')
  } else {
    sessionStorage.removeItem('fromDetail')
    sessionStorage.removeItem(SCROLL_KEY)
  }
})
</script>

<style scoped>
.resource-library {
  min-height: 100vh;
}

.content-card {
  width: 100%;
  padding: 2rem;
}

.search-section {
  /* background: #f2f2f7; */
  padding: 1.5rem 0 1rem 0;
}

.search-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 0 1rem;
}

.search-box {
  width: 100%;
}

.search-input {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.1);
  outline: none;
  padding: 12px 16px;
  font-size: 16px;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: all 0.2s ease;
}

.search-input:focus {
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.search-input::placeholder {
  color: #8E8E93;
  font-size: 16px;
}

.results-section {
  /* background: #f2f2f7; */
  min-height: 70vh;
  /* padding: 1.5rem; */
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  /* max-width: 1200px; */
  /* margin-left: auto; */
  /* margin-right: auto; */
}

.results-header h2 {
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
}

.results-count {
  color: #718096;
  font-size: 0.9rem;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.5rem;
  /* max-width: 1200px; */
  /* margin: 0 auto 3rem auto; */
}

.loading, .error, .empty-results, .initial-state {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.error {
  color: #e53e3e;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.3s ease;
}

.retry-btn:hover {
  background: #5a67d8;
}

.empty-results {
  color: #718096;
}

.empty-subtitle {
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.initial-state {
  color: #a0aec0;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 0.5rem;
}

.page-number {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-number:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.page-number.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-section {
    padding: 1.5rem 0 1rem 0;
  }

  .search-container {
    padding: 0 0.75rem;
  }

  .search-input {
    font-size: 16px; /* 防止iOS Safari缩放 */
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
  }
}
</style>
