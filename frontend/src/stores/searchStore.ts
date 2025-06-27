import { defineStore } from 'pinia'
import { reactive, ref, watch } from 'vue'
import { useNavigationStore } from './navigationStore'
import BangumiApiService, { type BangumiCalendarItem, convertSubjectToCalendarItem } from '../services/api'
import { debounce } from '../utils/debounce'

interface SearchPagination {
  current_page: number
  per_page: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

const STORAGE_KEY = 'ikuyo_search_state'

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

  // 获取导航store
  const navigationStore = useNavigationStore()

  // 检查是否应该恢复状态
  const checkShouldRestore = (): boolean => {
    // 使用导航store判断是否从详情页返回
    const shouldRestore = navigationStore.isReturningFromDetail('/library')
    console.log(`搜索页检查是否应该恢复状态: ${shouldRestore}`)
    return shouldRestore
  }

// 清空搜索状态
const clearSearchState =
    () => {
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

      // 清除sessionStorage
      try {
        window.sessionStorage.removeItem(STORAGE_KEY)
      } catch (err) {
        console.error('清除sessionStorage失败:', err)
      }
    }

// 防抖保存状态到sessionStorage
const saveToStorage = debounce(() => {
  try {
    const state = {
      searchQuery: searchQuery.value,
      searchResults: searchResults.value,
      pagination: {...pagination},
      hasSearched: hasSearched.value,
      timestamp: Date.now()
    } 
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    console.log('搜索状态已防抖保存到sessionStorage')
  } catch (err) {
    console.error('保存搜索状态失败:', err)
  }
}, 300)

// 从sessionStorage恢复状态
const restoreFromStorage = () => {
  try {
    const saved = window.sessionStorage.getItem(STORAGE_KEY)
    if (saved) {
      const state = JSON.parse(saved)

      // 检查导航来源，只有从详情页返回才恢复状态
      const shouldRestore = checkShouldRestore()

      if (shouldRestore && state.searchQuery) {
        searchQuery.value = state.searchQuery
        searchResults.value = state.searchResults || []
        hasSearched.value = state.hasSearched || false
        Object.assign(pagination, state.pagination || {})

        console.log('搜索状态已从sessionStorage恢复')
        return true // 返回true表示状态已恢复
      } else {
        // 不符合恢复条件，彻底清空状态和存储
        console.log('不符合状态恢复条件，清空所有状态')
        clearSearchState()
        return false // 返回false表示状态已清空
      }
    } else {
      // 没有保存的状态，确保当前状态是清空的
      console.log('没有保存的搜索状态')
      clearSearchState()
      return false
    }
  } catch (err) {
    console.error('恢复搜索状态失败:', err)
    clearSearchState()
    return false
  }
}

// 执行搜索
const performSearch =
    async (page: number = 1) => {
  if (!searchQuery.value.trim())
    return

        try {
      loading.value = true
      error.value = null
      hasSearched.value = true

      // 搜索获取bangumi_id列表
      const searchData =
          await BangumiApiService.searchLibrary(searchQuery.value, page, 12)

      // 更新分页信息
      Object.assign(pagination, searchData.pagination)

      if (searchData.bangumi_ids.length > 0) {
        // 批量获取番剧详情
        const subjects =
            await BangumiApiService.batchGetSubjects(searchData.bangumi_ids)

        // 转换为AnimeCard兼容格式
        searchResults.value =
            subjects.map(subject => convertSubjectToCalendarItem(subject))
      }
      else {searchResults.value = []}

      // 保存状态
      saveToStorage()

    } catch (err) {
      console.error('搜索失败:', err)
      error.value = '搜索失败，请检查网络连接'
    } finally {
      loading.value = false
    }
}

// 设置搜索关键词
const setSearchQuery =
    (query: string) => {
      searchQuery.value = query
    }

// 跳转到页面
const goToPage =
    (page: number) => {
      if (page >= 1 && page <= pagination.total_pages) {
        performSearch(page)
      }
    }

// 获取可见的页码
const getVisiblePages =
    () => {
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

// 监听关键状态变化，自动保存
watch([searchQuery, searchResults, pagination], () => {
  if (hasSearched.value) {
    saveToStorage()
  }
}, {deep: true})

    return {
  // 状态
  searchQuery, searchResults, loading, error, hasSearched, pagination,

      // 方法
      restoreFromStorage, clearSearchState, performSearch, setSearchQuery,
      goToPage, getVisiblePages
    }
})