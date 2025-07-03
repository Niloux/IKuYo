import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.config.errorHandler = (err, vm, info) => {
  // 处理错误，例如：报告给错误监控服务
  console.error('Vue 应用错误:', err, vm, info);
  // 可以在这里添加用户友好的错误提示
  // alert('应用发生错误，请刷新页面或联系管理员。');
};

app.mount('#app')
