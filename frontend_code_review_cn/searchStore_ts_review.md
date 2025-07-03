# `frontend/src/stores/searchStore.ts` 代码审查

## 分析

`searchStore.ts` 文件定义了一个 Pinia Store，用于管理应用程序的搜索功能，包括搜索查询、搜索结果、加载状态、错误信息以及分页数据。

1.  **状态定义**: 定义了 `searchQuery`（搜索关键词）、`searchResults`（搜索结果）、`loading`（加载状态）、`error`（错误信息）、`hasSearched`（是否已执行搜索）以及 `pagination`（分页信息）等响应式状态。
2.  **搜索逻辑**: `performSearch` 方法是核心，它首先调用 `BangumiApiService.searchLibrary` 获取番剧 ID 列表和分页信息，然后通过 `BangumiApiService.batchGetSubjects` 批量获取番剧详情，最后将结果转换为 `BangumiCalendarItem` 格式。
3.  **分页管理**: `pagination` 使用 `reactive` 定义，并提供了 `goToPage` 和 `getVisiblePages` 方法来处理分页逻辑。
4.  **状态清空**: `clearSearchState` 方法用于重置所有搜索相关的状态。

## 建议和理由

### 1. `performSearch` 中的错误处理

*   **建议**: 当前 `performSearch` 中的错误处理只是简单地 `console.error` 并设置 `error.value`。可以考虑更细致的错误提示，例如区分网络错误和后端返回的业务错误。
*   **理由**: 友好的错误提示能提升用户体验。例如，可以根据 `err` 对象的结构判断是网络问题还是服务器返回的特定错误信息，并显示更具体的提示。

### 2. `getVisiblePages` 的逻辑优化

*   **建议**: `getVisiblePages` 方法用于生成可见的页码列表。当前的逻辑在页码较少时表现良好，但在总页数非常多时，`start` 和 `end` 的计算可能导致显示的页码范围不够灵活（例如，总是显示当前页前后各2页）。
*   **理由**: 考虑实现更通用的分页组件逻辑，例如：
    *   在页码较少时显示所有页码。
    *   在页码较多时，显示首尾页、当前页附近页码，并用省略号表示中间省略的页码（例如 `1 ... 5 6 7 ... 100`）。这通常需要更复杂的逻辑来计算省略号的位置和显示的页码范围。

### 3. `hasSearched` 状态的必要性

*   **建议**: `hasSearched` 状态用于指示是否已执行过搜索。这个状态可以通过检查 `searchQuery.value` 是否为空或 `searchResults.value` 是否为空来推断。
*   **理由**: 冗余状态会增加维护成本。如果 `hasSearched` 只是为了控制 UI 的显示（例如，在未搜索时显示提示信息），那么可以直接通过 `computed` 属性来派生，例如 `const showNoResults = computed(() => !loading.value && hasSearched.value && searchResults.value.length === 0)`。

### 4. `performSearch` 的防抖/节流

*   **建议**: 如果 `performSearch` 会在用户输入 `searchQuery` 时频繁触发（例如，通过 `watch` 监听 `searchQuery` 的变化），建议对 `performSearch` 进行防抖（debounce）处理。
*   **理由**: 防抖可以减少不必要的 API 请求，尤其是在用户快速输入时，从而减轻服务器压力，提高前端性能和用户体验。可以在 `setSearchQuery` 中触发防抖的搜索。

### 5. `pagination` 对象的重置

*   **建议**: 在 `clearSearchState` 中，使用 `Object.assign(pagination, {...})` 来重置 `pagination` 对象。这种方式是正确的，因为它保留了 `pagination` 的响应性。
*   **理由**: 保持这种重置方式，确保 `pagination` 仍然是 `reactive` 对象，并且其引用没有改变，避免在组件中因引用丢失而导致响应性失效。

### 6. 类型定义的一致性

*   **建议**: 确保 `SearchPagination` 接口与后端实际返回的分页数据结构完全一致。如果后端返回的字段名或类型有差异，应及时调整。
*   **理由**: 严格的类型定义有助于在开发阶段捕获错误，提高代码的健壮性。

### 总结

`searchStore.ts` 很好地封装了搜索和分页逻辑。主要的改进点在于优化 `getVisiblePages` 的分页显示逻辑，考虑对搜索请求进行防抖处理，以及审查 `hasSearched` 状态的必要性，以进一步提高用户体验和代码效率。
