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
      meta: {title: 'IKuYo - 追番助手', keepAlive: true}
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
      meta: {title: '资源库', keepAlive: true}
    },
    {
      path: '/library/detail/:id',
      name: 'library-detail',
      component: () => import('../views/AnimeDetailView.vue'),
      meta: {title: '番剧资源', showResources: true}
    },
    {
      path: '/tasks',
      name: 'task-management',
      component: () => import('../views/TaskManagementView.vue'),
      meta: {title: '任务管理'}
    },
    {
      path: '/subscription',
      name: 'subscription',
      component: () => import('../views/SubscriptionView.vue'),
      meta: { title: '我的订阅', keepAlive: true }
    },
    {
      path: '/:pathMatch(.*)*', // 捕获所有未匹配的路由
      name: 'NotFound',
      component: () => import('../views/NotFoundView.vue'),
      meta: { title: '页面未找到' }
    }
  ]
})

// 全局路由守卫 - 设置页面标题
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }

  // 预取详情页chunk：如即将进入anime-detail或library-detail，提前加载详情页和相关组件
  if (to.name === 'anime-detail' || to.name === 'library-detail') {
    // 预加载详情页视图
    import('../views/AnimeDetailView.vue')
    // 预加载详情页主要异步组件
    import('../components/EpisodeDisplay.vue')
    import('../components/AnimeResourcesList.vue')
  }
  // 预取任务管理页chunk
  if (to.name === 'task-management') {
    import('../views/TaskManagementView.vue')
    import('../components/TaskModal.vue')
    import('../components/ScheduledJobModal.vue')
  }
  // 预取资源库页chunk
  if (to.name === 'resource-library') {
    import('../views/ResourceLibraryView.vue')
    import('../components/AnimeCard.vue')
  }
  // 预取订阅页chunk
  if (to.name === 'subscription') {
    import('../views/SubscriptionView.vue')
    import('../components/AnimeCard.vue')
  }

  // 导航来源追踪现在完全由组件内的onBeforeRouteLeave处理
  // 不在这里设置，避免冲突

  next()
})

export default router
