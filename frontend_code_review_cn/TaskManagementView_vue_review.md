# `frontend/src/views/TaskManagementView.vue` 代码审查

## 分析

`TaskManagementView.vue` 组件是任务管理页面，负责展示和管理即时爬虫任务和定时计划任务。它集成了任务列表展示、任务创建/编辑模态框、任务状态更新以及 WebSocket 实时进度监听。

1.  **状态管理**: 通过 `useTaskStore` 获取和管理任务及计划任务的列表、加载状态和错误信息。
2.  **组件使用**: 使用 `TaskTable` 和 `ScheduledJobTable` 展示任务列表，使用 `TaskModal` 和 `ScheduledJobModal` 处理任务的创建和编辑。
3.  **任务操作**: 提供了创建、取消即时任务，以及创建、更新、删除、切换定时任务状态的功能。
4.  **表单验证**: 实现了 `validateCreateTaskForm` 和 `validateScheduledJobForm` 进行客户端表单验证。
5.  **WebSocket 监听**: 使用 `watch` 监听 `taskStore.tasks` 的变化，自动为进行中的任务建立 WebSocket 连接以获取实时进度更新，并在组件卸载时清理所有连接。
6.  **辅助函数**: 内部定义了 `getParameter`、`formatDateTime` 和 `formatTime` 等辅助函数。
7.  **样式**: 样式通过 `style src="../assets/task.css"` 外部引入。

## 建议和理由

### 1. 辅助函数的重复定义

*   **建议**: `getParameter`、`formatDateTime` 和 `formatTime` 这三个辅助函数在 `TaskManagementView.vue` 中被重新定义了，而它们在 `frontend/src/utils/taskUtils.ts` 中已经存在。
*   **理由**: 代码重复是维护的敌人。应该从 `utils/taskUtils.ts` 中导入并使用这些函数，而不是在组件内部重新定义。这可以确保逻辑的一致性，减少代码量，并使未来的修改更加集中。

### 2. WebSocket 连接管理逻辑的职责划分

*   **建议**: `TaskManagementView.vue` 中通过 `watch` 监听任务状态并调用 `taskStore.startTaskProgressWs` 和 `taskStore.stopTaskProgressWs` 来管理 WebSocket 连接。同时，组件内部还维护了一个 `activeWebSockets` 的 `Map`，并在 `setupTaskWebSocket` 中直接操作 WebSocket 实例。
*   **理由**: `taskStore.ts` 中已经包含了 `startTaskProgressWs`、`stopTaskProgressWs` 和 `stopAllTaskProgressWs` 等方法，并且 `taskStore.startTaskProgressWs` 内部已经处理了 WebSocket 实例的创建和事件监听。`TaskManagementView.vue` 中的 `setupTaskWebSocket` 和 `activeWebSockets` 变量似乎与 Store 中的逻辑存在重复或职责不清。建议：
    *   **将所有 WebSocket 连接管理逻辑完全封装在 `taskStore` 中**。组件只负责调用 Store 提供的方法（如 `taskStore.startTaskProgressWs(taskId)`），而不需要关心 WebSocket 实例的内部管理（如 `activeWebSockets` Map）。
    *   确保 `taskStore.startTaskProgressWs` 能够处理重复连接的场景，并且在任务状态变为完成/失败/取消时，Store 内部能够自动关闭并清理对应的 WebSocket 连接。
    *   组件的 `onUnmounted` 钩子只需调用 `taskStore.stopAllTaskProgressWs()`。

### 3. 表单验证的改进

*   **建议**: 当前的表单验证是手动编写的，并且错误信息直接存储在 `createTaskFormErrors` 和 `scheduledJobFormErrors` 中。对于更复杂的表单，这种方式可能变得冗长和难以维护。
*   **理由**: 考虑使用成熟的表单验证库（如 VeeValidate, Zod, Yup 等）来简化验证逻辑。这些库通常提供更声明式的验证规则、更好的错误信息管理和与 Vue 表单的双向绑定集成。

### 4. 用户反馈机制

*   **建议**: 当前的成功/失败提示使用了原生的 `alert()` 函数。这会中断用户操作，并且样式不可控。
*   **理由**: 建议使用更友好的非阻塞式通知组件（如 Toast、Snackbar 或 Message 组件）来提供用户反馈。这可以提升用户体验，并使通知样式与应用程序整体风格保持一致。

### 5. 任务/计划任务列表的更新策略

*   **建议**: 在创建、更新、删除任务/计划任务后，都调用了 `fetchTasks()` 或 `fetchScheduledJobs()` 来刷新整个列表。这在数据量较小时可能不是问题，但对于大型列表，可能会导致性能开销。
*   **理由**: 考虑更精细的列表更新策略，例如：
    *   **创建**: 将新创建的任务/计划任务添加到现有列表的开头或末尾，而不是重新获取整个列表。
    *   **更新**: 在现有列表中找到对应的任务/计划任务，并更新其属性。
    *   **删除**: 从现有列表中移除对应的任务/计划任务。
    这种局部更新可以减少 API 请求量，提高用户界面的响应速度。

### 6. `parameters_json` 的处理

*   **建议**: 在 `ScheduledJobModal` 中，`parameters` 字段被处理为 `parameters_json` 字符串，并在提交时进行 `JSON.parse`。这增加了手动处理 JSON 字符串的复杂性。
*   **理由**: 如果 `parameters` 始终是 JSON 对象，可以考虑在表单组件中直接使用一个 JSON 编辑器组件，或者在数据绑定时自动进行 JSON 字符串和对象的转换，减少手动解析的步骤。

### 7. 确认对话框

*   **建议**: `cancelTask` 和 `deleteScheduledJob` 中使用了原生的 `confirm()` 对话框。
*   **理由**: 建议使用自定义的模态确认对话框，以提供更一致的用户界面和更好的用户体验。

### 总结

`TaskManagementView.vue` 是一个功能丰富的管理界面，集成了任务和计划任务的 CRUD 操作以及 WebSocket 实时更新。主要的改进点在于消除代码重复（辅助函数），优化 WebSocket 连接管理的职责划分，改进用户反馈机制，并考虑更高效的列表更新策略，以提高代码的可维护性、用户体验和性能。
