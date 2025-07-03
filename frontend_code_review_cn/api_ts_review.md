# `frontend/src/services/api.ts` 代码审查

## 分析

`api.ts` 文件是应用程序的核心 API 服务模块，负责处理与后端 Bangumi 相关接口的通信。它使用了 `axios` 库进行 HTTP 请求，并定义了相关的 TypeScript 类型。

1.  **Axios 实例**: 创建了一个 `apiClient` 的 Axios 实例，配置了 `baseURL`、`timeout` 和 `headers`。
2.  **响应拦截器**: 配置了一个响应拦截器，用于统一处理 API 响应，直接返回 `response.data`，并在请求失败时打印错误信息并拒绝 Promise。
3.  **类型定义**: 定义了多种与 Bangumi 相关的 TypeScript 接口，如 `ApiResponse`、`BangumiCalendarItem`、`BangumiSubject` 等，用于规范数据结构。
4.  **数据转换工具**: 提供了 `convertSubjectToCalendarItem` 函数，用于将 `BangumiSubject` 转换为 `BangumiCalendarItem`。
5.  **BangumiApiService**: 封装了多个与 Bangumi API 交互的方法，包括获取日历、番剧详情、集数可用性、章节信息、资源列表和搜索功能。
6.  **批量获取**: `batchGetSubjects` 方法通过 `Promise.allSettled` 并发调用 `getSubject` 来实现批量获取番剧详情，并处理了成功和失败的结果。

## 建议和理由

### 1. `API_BASE_URL` 的配置

*   **建议**: `API_BASE_URL` 目前是硬编码的 `http://127.0.0.1:8000/api/v1`。在实际部署中，后端 API 的地址可能会根据环境（开发、测试、生产）而变化。
*   **理由**: 建议将 `API_BASE_URL` 从环境变量中读取（例如，使用 `import.meta.env.VITE_API_BASE_URL`，如果使用 Vite），这样可以方便地在不同环境中切换 API 地址，而无需修改代码。

### 2. 响应拦截器的错误处理

*   **建议**: 当前的错误处理只是简单地 `console.error` 并 `Promise.reject(error)`。在实际应用中，可能需要更细致的错误处理，例如：
    *   根据 HTTP 状态码（如 401 未授权、403 禁止访问、404 未找到、500 服务器错误）进行不同的处理。
    *   向用户显示友好的错误提示（例如，使用通知组件或 Toast）。
    *   对于某些特定错误（如认证失败），可以进行重定向到登录页面的操作。
*   **理由**: 统一且完善的错误处理机制可以提升用户体验，并简化组件中的错误处理逻辑，避免在每个 API 调用处重复编写错误处理代码。

### 3. `ApiResponse` 泛型和数据提取

*   **建议**: `ApiResponse<T = any>` 中的 `T = any` 使得 `data` 字段的类型不够具体。在响应拦截器中直接 `return response.data`，这意味着所有 API 方法的返回值都将是 `ApiResponse<T>` 中的 `data` 部分。
*   **理由**: 这种设计是合理的，但需要确保后端响应始终符合 `ApiResponse` 的结构。如果后端响应有时不包含 `data` 字段，或者 `data` 字段的类型与 `T` 不符，可能会导致类型不匹配。可以考虑在每个 API 方法中明确指定 `ApiResponse` 的泛型类型，以增强类型安全性。

### 4. `BangumiEpisodesResponse` 的定义与使用

*   **建议**: `BangumiEpisodesResponse` 被定义为 `ApiResponse<BangumiEpisode[]> & { total: number }`，但在 `getBangumiEpisodes` 方法中，返回的是 `{data: response.data, total: response.total}`。这表明后端返回的结构是 `{ success: boolean, message: string, data: BangumiEpisode[], total: number }`。
*   **理由**: 如果 `ApiResponse` 总是包含 `success` 和 `message`，并且 `data` 是实际的数据，那么 `BangumiEpisodesResponse` 的定义可能需要更精确地反映后端结构，或者 `ApiResponse` 本身可以包含 `total` 字段（如果这是通用分页响应的一部分）。确保前端类型定义与后端实际返回的数据结构完全一致，可以避免潜在的运行时错误。

### 5. `getAnimeResources` 中的 `URLSearchParams`

*   **建议**: 在 `getAnimeResources` 方法中，手动构建 `URLSearchParams` 并拼接 URL。Axios 允许通过 `params` 选项自动处理查询参数。
*   **理由**: 使用 Axios 的 `params` 选项更简洁、更安全，它会自动处理参数的编码和拼接，避免手动构建 URL 时可能出现的错误。
    ```typescript
    static async getAnimeResources(bangumiId: number, options?: {
      resolution?: string,
      subtitle_type?: string,
      limit?: number,
      offset?: number
    }): Promise<EpisodeResourcesData> {
      const params: Record<string, any> = {};
      if (options?.resolution) params.resolution = options.resolution;
      if (options?.subtitle_type) params.subtitle_type = options.subtitle_type;
      if (options?.limit) params.limit = options.limit;
      if (options?.offset) params.offset = options.offset;

      const response: ApiResponse<EpisodeResourcesData> = await apiClient.get(
          `/animes/${bangumiId}/resources`, { params });
      return response.data;
    }
    ```

### 6. `batchGetSubjects` 的错误处理

*   **建议**: `batchGetSubjects` 使用 `Promise.allSettled` 来处理并发请求，这是一个很好的实践，因为它不会因为单个请求失败而中断整个批量操作。当前的错误处理只是 `console.error` 并 `throw error`。
*   **理由**: 可以考虑在 `catch` 块中对错误进行更详细的日志记录，或者根据业务需求，将失败的请求信息返回给调用方，以便进行更精细的错误展示或重试机制。

### 总结

`api.ts` 文件提供了良好的 API 封装和类型定义。主要的改进点在于增强配置的灵活性（`API_BASE_URL`）、完善错误处理机制、优化查询参数的构建方式，以及确保类型定义与后端响应的精确匹配。
