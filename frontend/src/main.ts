import './assets/main.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { ElMessage } from 'element-plus'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 全局注册ElMessage为window.$toast
interface Toast {
  error: (msg: string, opts?: Record<string, any>) => void
  info: (msg: string, opts?: Record<string, any>) => void
  success: (msg: string, opts?: Record<string, any>) => void
}
declare global {
  interface Window {
    $toast: Toast
  }
}
window.$toast = {
  error: (msg: string, opts = {}) => ElMessage.error({ message: msg, duration: 2500, ...opts }),
  info: (msg: string, opts = {}) => ElMessage.info({ message: msg, duration: 2500, ...opts }),
  success: (msg: string, opts = {}) => ElMessage.success({ message: msg, duration: 2500, ...opts }),
}

app.config.errorHandler = (err, vm, info) => {
  // 处理错误，例如：报告给错误监控服务
  console.error('Vue 应用错误:', err, vm, info);
  // 可以在这里添加用户友好的错误提示
  // alert('应用发生错误，请刷新页面或联系管理员。');
};

app.mount('#app')
