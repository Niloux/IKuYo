# `frontend/src/components/AnimeCard.vue` 代码审查

## 分析

`AnimeCard.vue` 组件用于展示单个番剧的卡片信息，包括封面、标题、副标题、评分和播出日期。它设计为可复用组件，并考虑了图片加载优化和错误处理。

1.  **Props 定义**: 接收 `anime` (类型为 `BangumiCalendarItem`) 和 `shouldLoadImage` (布尔值，默认为 `true`) 作为 props。
2.  **事件触发**: 触发 `click` 和 `imageLoad` 事件。
3.  **图片加载**: 根据 `shouldLoadImage` 决定是否加载图片，否则显示“加载中...”的占位符。
4.  **图片处理**: `convertToHttps` 函数用于将 HTTP 图片 URL 转换为 HTTPS，以避免潜在的 CORS 或混合内容问题。`imageUrl` 计算属性处理图片 URL 的逻辑，并在无图片时使用 `defaultCover`。
5.  **图片错误处理**: `onImageError` 函数在图片加载失败时将图片元素隐藏。
6.  **数据格式化**: `formatAirDate` 函数用于格式化播出日期。
7.  **样式**: 样式使用 `scoped`，包含了卡片布局、图片比例、信息展示、评分徽章和响应式设计。

## 建议和理由

### 1. 图片加载策略优化

*   **建议**: `shouldLoadImage` prop 用于实现分批加载，这是一种手动控制图片加载的方式。可以考虑结合浏览器原生的懒加载功能 (`loading="lazy"`) 或 Intersection Observer API 来实现更高效和自动化的图片懒加载。
*   **理由**:
    *   **原生懒加载**: `loading="lazy"` 是一个简单且高效的解决方案，浏览器会自动处理图片在进入视口时加载，无需额外的 JavaScript 逻辑。
    *   **Intersection Observer**: 对于更复杂的懒加载需求（例如，需要精确控制加载时机或加载动画），Intersection Observer API 提供了更强大的能力。
    *   **移除 `shouldLoadImage`**: 如果采用原生懒加载或 Intersection Observer，`shouldLoadImage` prop 及其相关的逻辑可以被移除，简化组件。

### 2. 图片加载失败处理

*   **建议**: 当前 `onImageError` 在图片加载失败时将图片 `display` 设置为 `none`。这会导致图片区域完全消失，可能造成布局跳动或用户体验不佳。
*   **理由**: 建议在图片加载失败时，显示一个默认的占位符图片（例如，一个通用的动漫封面图标或一个表示图片损坏的图标），而不是完全隐藏。这样可以保持布局稳定，并向用户提供更友好的视觉反馈。

### 3. `convertToHttps` 函数的健壮性

*   **建议**: `convertToHttps` 函数只处理了 `http://` 开头的 URL。如果 URL 已经是 `https://` 或者是一个相对路径，它会直接返回。这通常是正确的，但如果存在其他协议（如 `ftp://`）或不规范的 URL，可能需要更全面的处理。
*   **理由**: 确保该函数能够处理所有可能的输入，或者在文档中明确其预期输入。对于 Bangumi 的图片 URL，目前这种处理方式可能已经足够。

### 4. `formatAirDate` 的格式化一致性

*   **建议**: `formatAirDate` 使用 `toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })`。这与 `AnimeDetailView.vue` 中使用的 `toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })` 略有不同（`month: 'short'` vs `month: 'long'`）。
*   **理由**: 建议在整个应用程序中统一日期格式化方式，以确保用户界面的视觉一致性。可以在 `utils` 文件夹中创建一个通用的日期格式化工具函数，供所有组件使用。

### 5. `defaultCover` 的来源

*   **建议**: `defaultCover` 导入自 `../assets/ikuyo-avatar.png`。这是一个通用的头像图片，可能不适合作为番剧的默认封面。
*   **理由**: 建议使用一个更通用或专门设计的“无封面”图片作为默认封面，以提高用户界面的专业性。

### 6. CSS 变量的统一使用

*   **建议**: 样式中使用了许多硬编码的颜色值（如 `#f8f9fa`、`#6c757d`、`#3498db`）和间距值。虽然部分使用了 CSS 变量，但可以更广泛地使用。
*   **理由**: 建议将这些常用的颜色、字体大小、间距、阴影等定义为 CSS 变量，并在整个应用中复用。这有助于实现主题化，提高样式的一致性和可维护性。

### 总结

`AnimeCard.vue` 是一个设计良好的可复用组件，但在图片加载策略、图片错误处理和日期格式化一致性方面仍有优化空间。通过采用更现代的图片懒加载技术和统一的辅助函数，可以进一步提升组件的性能和可维护性。
