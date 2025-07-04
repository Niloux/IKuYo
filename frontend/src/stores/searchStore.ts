import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import BangumiApiService, { convertSubjectToCalendarItem } from '../services/bangumi/bangumiApiService'
import type { BangumiCalendarItem } from '../services/bangumi/bangumiTypes'

interface SearchPagination {
  current_page: number
  per_page: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const useSearchStore = defineStore('search', () => {
  // 搜索状态
  const searchQuery = ref('')
  const searchResults = ref<BangumiCalendarItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasSearched = ref(false)

  const pagination = reactive<SearchPagination>({
    current_page: 1,
    per_page: 12,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })

  // 清空搜索状态
  const clearSearchState = () => {
    searchQuery.value = ''
    searchResults.value = []
    hasSearched.value = false
    loading.value = false
    error.value = null
    Object.assign(pagination, {
      current_page: 1,
      per_page: 12,
      total: 0,
      total_pages: 0,
      has_next: false,
      has_prev: false
    })
  }

  // 执行搜索
  const performSearch = async (
    page: number = 1,
    options?: { debounce?: boolean; throttle?: boolean; delay?: number }
  ) => {
    if (!searchQuery.value.trim()) return

    try {
      loading.value = true
      error.value = null
      hasSearched.value = true

      // 搜索获取bangumi_id列表
      const searchData = await BangumiApiService.searchLibrary(searchQuery.value, page, 12, options)

      // 更新分页信息
      Object.assign(pagination, searchData.pagination)

      if (searchData.bangumi_ids.length > 0) {
        // 批量获取番剧详情
        const { success: subjects } =
          await BangumiApiService.batchGetSubjects(searchData.bangumi_ids)

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

  // 设置搜索关键词
  const setSearchQuery = (query: string) => {
    searchQuery.value = query
  }

  // 跳转到页面
  const goToPage = (page: number, options?: { debounce?: boolean; throttle?: boolean; delay?: number }) => {
    if (page >= 1 && page <= pagination.total_pages) {
      performSearch(page, options)
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

  return {
    // 状态
    searchQuery, searchResults, loading, error, hasSearched, pagination,

    // 方法
    clearSearchState, performSearch, setSearchQuery,
    goToPage, getVisiblePages
  }
})
