# `frontend/src/views/HomeView.vue` 代码审查

## 分析

`HomeView.vue` 是应用程序的主页视图，负责显示每日放送的番剧日历。它集成了数据加载、错误处理、滚动位置管理、图片分批加载优化以及响应式设计。

1.  **数据源**: 通过 `useHomeStore` 获取日历数据、加载状态和错误信息，并使用 `storeToRefs` 保持响应性。
2.  **条件渲染**: 根据 `loading` 和 `error` 状态显示不同的 UI（加载中、错误信息、内容）。
3.  **组件使用**: 集成了 `WeekNavigation`、`ScrollToTopButton` 和 `AnimeCard` 等子组件。
4.  **日历排序**: `sortCalendarByWeek` 函数根据当前日期对日历数据进行排序，将“今天”的番剧放在最前面。
5.  **图片分批加载**: 实现了 `isFirstBatch` 和 `onImageLoad` 逻辑，尝试分批加载 `AnimeCard` 中的图片，以优化初始加载性能。
6.  **滚动位置管理**: 利用 `onBeforeRouteLeave` 保存滚动位置，并在 `onActivated` 中根据是否从详情页返回来恢复滚动位置或滚动到顶部，与 `keep-alive` 配合良好。
7.  **路由导航**: `goToDetail` 函数用于跳转到番剧详情页。
8.  **样式**: 样式使用 `scoped`，包含了加载/错误状态、日历容器、每日分区和番剧网格的样式，并有响应式媒体查询。

## 建议和理由

### 1. 数据加载逻辑的封装

*   **建议**: `loadCalendar` 函数目前直接在组件中调用 `BangumiApiService.getCalendar()` 并更新 `homeStore` 的状态。虽然功能上没问题，但将数据获取逻辑完全封装到 `homeStore` 的 `action` 中会更好。
*   **理由**: 如同在 `homeStore.ts` 的审查中提到的，将数据获取逻辑（包括 `loading` 和 `error` 状态的更新）集中到 Store 中，可以使组件更专注于 UI 渲染和用户交互，提高 Store 的内聚性和可测试性。组件只需调用 `homeStore.fetchCalendar()`。

### 2. `ensureScrollToTop` 的使用

*   **建议**: 在 `onActivated` 中，如果不是从详情页返回，调用了 `ensureScrollToTop()`。在 `scrollUtils.ts` 的审查中，我建议优化 `ensureScrollToTop` 的逻辑，使其只在 `requestAnimationFrame` 中执行一次。
*   **理由**: 确保 `ensureScrollToTop` 的行为符合预期，避免不必要的重复调用或潜在的性能开销。

### 3. 图片分批加载逻辑的健壮性

*   **建议**: `isFirstBatch` 和 `onImageLoad` 实现了图片分批加载。`totalFirstBatch` 的计算是总番剧数量的一半。这种基于数量的划分可能不总是最佳的，例如，如果前一半的番剧图片很小，而后一半的图片很大，优化效果可能不明显。
*   **理由**: 考虑更智能的分批加载策略，例如：
    *   **视口检测**: 使用 Intersection Observer API 来判断图片是否进入视口，只加载视口内的图片。
    *   **优先级**: 根据图片在页面中的位置（例如，首屏可见区域）来确定加载优先级。
    *   **骨架屏/占位符**: 在图片加载完成前显示骨架屏或低质量占位符，提升用户感知性能。
    *   **`loading="lazy"`**: 对于非关键图片，可以直接使用 `<img>` 标签的 `loading="lazy"` 属性，让浏览器自动处理懒加载。

### 4. `sessionStorage` 的使用

*   **建议**: 使用 `sessionStorage` 来标记是否从详情页返回，以控制滚动行为。这是一种有效的跨页面状态传递方式。
*   **理由**: 确保 `sessionStorage` 的键名（`fromDetail`）是唯一的，并且在不再需要时及时清除，避免不必要的存储占用。

### 5. `isToday` 和 `getDaysFromToday` 的日期处理

*   **建议**: `isToday` 和 `getDaysFromToday` 函数中，`new Date().getDay()` 返回的是 0-6（周日到周六），而 `weekdayId` 可能有不同的定义（例如，周一到周日为 1-7）。代码中通过 `adjustedWeekdayId = weekdayId === 0 ? 7 : weekdayId` 进行了调整，以统一为 1-7 的范围。
*   **理由**: 这种调整是必要的，以确保日期计算的准确性。保持这种清晰的转换逻辑。

### 6. CSS 变量的进一步使用

*   **建议**: 在样式中，可以进一步利用 CSS 变量来管理颜色、间距、阴影等，例如 `var(--color-error)`、`var(--shadow-md)` 等已经在使用，可以扩展到更多地方。
*   **理由**: 提高样式的一致性和可维护性。

### 7. `AnimeCard` 的 `key` 属性

*   **建议**: `AnimeCard` 的 `v-for` 中使用了 `anime.id` 作为 `key`，这是正确的做法。
*   **理由**: 使用唯一且稳定的 `key` 对于 Vue 列表渲染的性能优化至关重要，可以帮助 Vue 更高效地更新 DOM。

### 总结

`HomeView.vue` 是一个功能丰富的视图组件，在数据加载、滚动管理和图片优化方面做了很多工作。主要的改进点在于将数据获取逻辑完全封装到 Store 中，进一步优化图片加载策略，并持续关注代码的健壮性和可维护性。
