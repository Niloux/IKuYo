<template>
  <div class="resource-library">
    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-container">
        <h1 class="page-title">番剧资源库</h1>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索番剧名称..."
            class="search-input"
            @input="handleSearchInput"
            @keyup.enter="handleSearch"
          />
          <button 
            @click="handleSearch" 
            class="search-btn"
            :disabled="!searchQuery.trim() || loading"
          >
            搜索
          </button>
        </div>
      </div>
    </div>

    <!-- 搜索结果区域 -->
    <div class="results-section">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <p>正在搜索...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="handleSearch" class="retry-btn">重试</button>
      </div>

      <!-- 搜索结果 -->
      <div v-else-if="searchResults.length > 0">
        <div class="results-header">
          <h2>搜索结果</h2>
          <span class="results-count">
            找到 {{ pagination.total }} 个结果
          </span>
        </div>
        
        <!-- 番剧网格 -->
        <div class="anime-grid">
          <AnimeCard
            v-for="anime in searchResults"
            :key="anime.id"
            :anime="anime"
            @click="goToLibraryDetail(anime.id)"
          />
        </div>

        <!-- 分页组件 -->
        <div v-if="pagination.total_pages > 1" class="pagination">
          <button 
            @click="goToPage(pagination.current_page - 1)"
            :disabled="!pagination.has_prev"
            class="pagination-btn"
          >
            上一页
          </button>
          
          <div class="page-numbers">
            <span 
              v-for="page in getVisiblePages()"
              :key="page"
              :class="['page-number', { active: page === pagination.current_page }]"
              @click="goToPage(page)"
            >
              {{ page }}
            </span>
          </div>
          
          <button 
            @click="goToPage(pagination.current_page + 1)"
            :disabled="!pagination.has_next"
            class="pagination-btn"
          >
            下一页
          </button>
        </div>
      </div>

      <!-- 空搜索状态 -->
      <div v-else-if="hasSearched && searchResults.length === 0" class="empty-results">
        <p>没有找到相关番剧</p>
        <p class="empty-subtitle">尝试使用其他关键词搜索</p>
      </div>

      <!-- 初始状态 -->
      <div v-else class="initial-state">
        <p>输入番剧名称开始搜索</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '../components/AnimeCard.vue'
import BangumiApiService, { convertSubjectToCalendarItem, type BangumiCalendarItem } from '../services/api'

const router = useRouter()

// 响应式数据
const searchQuery = ref('')
const searchResults = ref<BangumiCalendarItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

const pagination = reactive({
  current_page: 1,
  per_page: 12,
  total: 0,
  total_pages: 0,
  has_next: false,
  has_prev: false
})

// 防抖处理
let searchTimeout: number | null = null

const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    if (searchQuery.value.trim()) {
      performSearch()
    }
  }, 300) as unknown as number
}

// 执行搜索
const performSearch = async (page: number = 1) => {
  if (!searchQuery.value.trim()) return

  try {
    loading.value = true
    error.value = null
    hasSearched.value = true

    // 搜索获取bangumi_id列表
    const searchData = await BangumiApiService.searchLibrary(searchQuery.value, page, 12)
    
    // 更新分页信息
    Object.assign(pagination, searchData.pagination)

    if (searchData.bangumi_ids.length > 0) {
      // 批量获取番剧详情
      const subjects = await BangumiApiService.batchGetSubjects(searchData.bangumi_ids)
      
      // 转换为AnimeCard兼容格式
      searchResults.value = subjects.map(subject => convertSubjectToCalendarItem(subject))
    } else {
      searchResults.value = []
    }

  } catch (err) {
    console.error('搜索失败:', err)
    error.value = '搜索失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

// 执行搜索的包装函数（用于事件处理）
const handleSearch = () => {
  performSearch()
}

// 跳转到页面
const goToPage = (page: number) => {
  if (page >= 1 && page <= pagination.total_pages) {
    performSearch(page)
  }
}

// 获取可见的页码
const getVisiblePages = () => {
  const pages = []
  const current = pagination.current_page
  const total = pagination.total_pages
  
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
}

// 跳转到资源库详情页
const goToLibraryDetail = (bangumiId: number) => {
  router.push(`/library/detail/${bangumiId}`)
}
</script>

<style scoped>
.resource-library {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.search-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 3rem 0;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  padding: 0 1rem;
}

.page-title {
  color: white;
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.search-box {
  display: flex;
  gap: 0.5rem;
  background: white;
  border-radius: 50px;
  padding: 0.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.875rem 1.5rem;
  font-size: 1rem;
  border-radius: 50px;
  background: transparent;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 50px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results-section {
  background: #f8fafc;
  min-height: 70vh;
  padding: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
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
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto 3rem auto;
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
  .page-title {
    font-size: 2rem;
  }
  
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1rem;
  }
  
  .search-box {
    flex-direction: column;
    border-radius: 1rem;
  }
  
  .search-input, .search-btn {
    border-radius: 0.5rem;
  }
}
</style> 