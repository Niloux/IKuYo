# .

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## 全局交互反馈机制说明

本项目前端实现了统一的全局交互反馈机制，包含：

- **全局Loading遮罩**：用于显示全局加载状态，调用`feedbackStore.showLoading()`/`hideLoading()`控制，主布局已挂载`<GlobalLoading />`。
- **全局Toast消息**：用于全局消息提示，调用`feedbackStore.showToast(message, type)`推送，主布局已挂载`<GlobalToast />`。
- **全局Error弹窗**：用于全局错误提示，调用`feedbackStore.showError(message)`推送，主布局已挂载`<GlobalError />`。

### 用法示例

```ts
import { useFeedbackStore } from '@/stores/feedbackStore';
const feedbackStore = useFeedbackStore();

// 显示全局Loading
feedbackStore.showLoading();
// 隐藏全局Loading
feedbackStore.hideLoading();

// 显示全局Toast
feedbackStore.showToast('操作成功', 'success');
feedbackStore.showToast('发生错误', 'error');

// 显示全局Error弹窗
feedbackStore.showError('系统异常，请重试');
// 关闭全局Error弹窗
feedbackStore.clearError();
```

### 注意事项
- 全局Loading、Toast、Error组件已在AppLayout.vue中全局挂载，无需重复引入。
- 全局axios拦截器已自动处理大部分API异常，业务层只需处理特殊场景。
- 资源详情页部分接口404已做白名单静默处理，不会弹窗。
