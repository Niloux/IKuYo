import {createRouter, createWebHistory} from 'vue-router'

import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
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
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router
