# `frontend/src/stores/homeStore.ts` 代码审查

## 分析

`homeStore.ts` 文件定义了一个 Pinia Store，用于管理主页相关的状态，特别是日历数据的缓存和滚动位置的保存。

1.  **状态定义**: 定义了 `loading`、`error`、`cachedCalendar`（日历数据缓存）、`hasCalendarData`（是否有日历数据）和 `savedScrollPosition`（滚动位置）等响应式状态。
2.  **方法**: 提供了 `clearCache`（清空缓存）、`setCalendarData`（设置日历数据）、`saveScrollPosition`（保存滚动位置）和 `getScrollPosition`（获取滚动位置）等方法。
3.  **目的**: 旨在通过缓存日历数据和保存滚动位置来优化用户体验，减少不必要的 API 请求和页面重绘。

## 建议和理由

### 1. 数据获取逻辑的集成

*   **建议**: 当前 Store 中定义了 `loading` 和 `error` 状态，但没有包含实际的日历数据获取（API 调用）逻辑。这意味着数据获取可能在组件中完成，然后通过 `setCalendarData` 更新 Store。
*   **理由**: 将数据获取逻辑（例如，调用 `BangumiApiService.getCalendar()`）封装到 Store 的一个 `action` 中，可以更好地集中管理数据流、加载状态和错误处理。这使得组件只负责调用 Store 的 action，而不需要关心数据获取的具体实现细节，从而提高代码的内聚性和可测试性。

### 2. `hasCalendarData` 的冗余

*   **建议**: `hasCalendarData` 状态可以通过 `cachedCalendar.value.length > 0` 来派生。这意味着 `hasCalendarData` 是一个冗余的状态。
*   **理由**: 冗余状态会增加维护成本，因为需要确保它始终与 `cachedCalendar` 的实际内容保持同步。可以将其转换为一个 `getter`，或者直接在需要的地方判断 `cachedCalendar` 的长度。

### 3. `getScrollPosition` 方法的必要性

*   **建议**: `getScrollPosition` 方法只是简单地返回 `savedScrollPosition.value`。在 Vue 3 和 Pinia 的组合式 API 中，可以直接从 Store 实例中访问 `savedScrollPosition`。
*   **理由**: 如果没有额外的逻辑或计算，这种简单的 getter 方法是不必要的，直接访问状态可以使代码更简洁。例如，在组件中可以通过 `store.savedScrollPosition` 直接获取值。

### 4. 错误状态 `error` 的使用

*   **建议**: `error` 状态目前在 Store 中定义了，但没有在任何方法中使用。如果数据获取逻辑被集成到 Store 中，应该在 API 请求失败时更新 `error` 状态。
*   **理由**: 统一的错误处理机制可以帮助组件更好地响应和显示错误信息，提升用户体验。

### 5. 命名和结构优化示例

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { BangumiWeekday } from '../services/api'
import { BangumiApiService } from '../services/api' // 假设已导入API服务

export const useHomeStore = defineStore('home', () => {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const calendarData = ref<BangumiWeekday[]>([]) // 更名为 calendarData，表示实际数据
  const savedScrollPosition = ref(0)

  // Getter: 是否有日历数据
  const hasCalendarData = computed(() => calendarData.value.length > 0)

  // Action: 获取日历数据
  const fetchCalendar = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await BangumiApiService.getCalendar()
      calendarData.value = data
    } catch (err: any) {
      error.value = err.message || '获取日历数据失败'
      console.error('获取日历数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // Action: 清空缓存数据
  const clearCache = () => {
    calendarData.value = []
    savedScrollPosition.value = 0
  }

  // Action: 保存滚动位置
  const saveScrollPosition = (position: number) => {
    savedScrollPosition.value = position
  }

  return {
    loading,
    error,
    calendarData,
    savedScrollPosition,
    hasCalendarData, // 作为 getter 暴露
    fetchCalendar,
    clearCache,
    saveScrollPosition,
  }
})
```

### 总结

`homeStore.ts` 的设计思路是合理的，通过 Pinia 实现了状态管理和缓存。主要的改进点在于将数据获取逻辑集成到 Store 中，消除冗余状态，并优化方法的必要性，从而提高 Store 的内聚性、可维护性和代码简洁性。
