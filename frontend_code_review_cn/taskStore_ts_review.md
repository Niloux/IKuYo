# `frontend/src/stores/taskStore.ts` 代码审查

## 分析

`taskStore.ts` 文件定义了一个 Pinia Store，用于管理应用程序中的即时爬虫任务和定时计划任务。它封装了与 `CrawlerApiService` 的交互，并处理了任务列表、加载状态、错误信息以及 WebSocket 进度更新。

1.  **状态定义**: 定义了 `tasks`（即时任务列表）、`scheduledJobs`（计划任务列表）、`isLoadingTasks`、`isLoadingScheduledJobs`（加载状态）、`error`（错误信息）、`currentPage` 和 `pageSize` 等响应式状态。
2.  **即时任务操作**: 包含了 `fetchTasks`（获取任务列表）、`setCurrentPage`（设置当前页码）、`createTask`（创建任务）和 `cancelTask`（取消任务）等方法。
3.  **计划任务操作**: 包含了 `fetchScheduledJobs`（获取计划任务列表）、`createScheduledJob`（创建计划任务）、`updateScheduledJob`（更新计划任务）、`deleteScheduledJob`（删除计划任务）和 `toggleScheduledJob`（切换计划任务状态）等方法。
4.  **WebSocket 管理**: 提供了 `connectTaskProgressWs`（连接 WebSocket）、`startTaskProgressWs`（启动 WebSocket 监听）、`stopTaskProgressWs`（停止单个 WebSocket 监听）和 `stopAllTaskProgressWs`（停止所有 WebSocket 监听）等方法，用于实时更新任务进度。
5.  **错误处理**: 在每个异步操作中都包含了 `try...catch` 块，用于捕获错误并设置 `error` 状态。

## 建议和理由

### 1. 错误处理的统一性与细化

*   **建议**: 当前每个异步操作的 `catch` 块都重复了 `error.value = err.message || '...' ` 和 `console.error`。这导致了代码冗余。
*   **理由**: 建议创建一个通用的错误处理函数或辅助方法，在 Store 内部或外部统一处理 API 请求的错误。这样可以减少重复代码，并确保错误处理逻辑的一致性。例如，可以根据错误类型（网络错误、后端返回的业务错误）显示不同的用户提示。

### 2. `fetchTasks` 和 `fetchScheduledJobs` 的刷新策略

*   **建议**: 在 `createTask`、`createScheduledJob`、`updateScheduledJob`、`deleteScheduledJob` 和 `toggleScheduledJob` 等操作成功后，都调用了 `await fetchTasks()` 或 `await fetchScheduledJobs()` 来刷新列表。这在某些情况下可能导致不必要的全量数据重新获取。
*   **理由**: 对于单个任务或计划任务的创建、更新、删除操作，可以考虑更精细的列表更新策略，例如：
    *   **创建**: 将新创建的任务/计划任务添加到现有列表的开头或末尾。
    *   **更新**: 在现有列表中找到对应的任务/计划任务，并更新其属性。
    *   **删除**: 从现有列表中移除对应的任务/计划任务。
    这种局部更新可以减少 API 请求量，提高用户界面的响应速度。当然，如果后端分页或过滤逻辑复杂，全量刷新可能是更简单的选择，但应权衡性能。

### 3. WebSocket 连接的管理

*   **建议**: `taskProgressWsMap` 用于管理 WebSocket 连接。`startTaskProgressWs` 在任务完成/失败/取消时会自动断开连接，这是很好的实践。但需要确保在组件卸载时，所有相关的 WebSocket 连接都被 `stopAllTaskProgressWs` 或 `stopTaskProgressWs` 清理，以避免内存泄漏和不必要的网络连接。
*   **理由**: 确保 WebSocket 连接的生命周期与组件或页面的生命周期同步，可以有效管理资源，避免性能问题。

### 4. `connectTaskProgressWs` 方法的职责

*   **建议**: `connectTaskProgressWs` 方法接收了 `onMessageCallback`、`onErrorCallback` 和 `onCloseCallback` 作为参数，并在内部设置了 WebSocket 的事件监听器。而 `startTaskProgressWs` 又在内部重新设置了这些监听器。
*   **理由**: 这种设计可能导致混淆或重复设置监听器。建议 `CrawlerApiService.connectTaskProgressWs` 仅负责返回 WebSocket 实例，而所有事件监听器的设置和处理逻辑都集中在 `taskStore` 的 `startTaskProgressWs` 方法中。这样可以更好地分离职责，使代码更易于理解和维护。

### 5. `currentPage` 和 `pageSize` 的使用

*   **建议**: `fetchTasks` 方法使用了 `currentPage` 和 `pageSize`。如果任务列表支持总页数或总条数，可以在 Store 中添加相应的状态来管理分页信息，并提供 `setPageSize` 等方法。
*   **理由**: 完善的分页管理可以更好地支持任务列表的展示和交互，例如显示总页数、跳转到指定页等。

### 6. `TaskResponse` 中 `parameters` 字段的类型

*   **建议**: `TaskResponse` 中的 `parameters` 字段被定义为 `string`。如果它实际上是 JSON 字符串，并且前端需要解析其内容，那么在 Store 中获取到数据后，可以考虑将其解析为对象。
*   **理由**: 将 JSON 字符串解析为对象可以方便前端直接访问其内部属性，避免在组件中重复解析。

### 总结

`taskStore.ts` 在任务和计划任务管理方面功能全面，特别是 WebSocket 的集成是一个亮点。主要的改进点在于优化错误处理的统一性，考虑更精细的列表刷新策略，以及进一步理清 WebSocket 连接管理中方法的职责，以提高代码的健壮性和可维护性。
