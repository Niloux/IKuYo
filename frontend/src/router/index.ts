import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  // 禁用默认的滚动行为，完全由我们手动管理
  scrollBehavior() {
    // 返回false来阻止任何自动滚动
    return false
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: {title: 'IKuYo - 追番助手'}
    },
    {
      path: '/anime/:id',
      name: 'anime-detail',
      component: () => import('../views/AnimeDetailView.vue'),
      meta: {title: '番剧详情'}
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
      meta: {title: '关于'}
    },
    {
      path: '/library',
      name: 'resource-library',
      component: () => import('../views/ResourceLibraryView.vue'),
      meta: {title: '资源库'}
    },
    {
      path: '/library/detail/:id',
      name: 'library-detail',
      component: () => import('../views/AnimeDetailView.vue'),
      meta: {title: '番剧资源', showResources: true}
    }
  ]
})

// 全局路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }

  // 导航来源追踪现在完全由组件内的onBeforeRouteLeave处理
  // 不在这里设置，避免冲突

  next()
})

export default router
