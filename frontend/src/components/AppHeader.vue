<template>
  <header class="app-header">
    <div class="header-container">
      <!-- 品牌标识 -->
      <div class="brand">
        <RouterLink to="/" class="brand-link">
          <div class="brand-icon">
            <img src="@/assets/ikuyo-avatar.png" alt="IKuYo" class="logo" />
          </div>
          <div class="brand-text">
            <h1 class="brand-title">IKuYo</h1>
            <span class="brand-subtitle">追番助手</span>
          </div>
        </RouterLink>
      </div>

      <!-- 导航菜单 -->
      <nav class="nav-menu">
        <RouterLink to="/" class="nav-item" active-class="active">
          <span class="nav-text">首页</span>
        </RouterLink>
        <RouterLink to="/library" class="nav-item" active-class="active">
          <span class="nav-text">资源库</span>
        </RouterLink>
        <RouterLink to="/subscription" class="nav-item" active-class="active">
          <span class="nav-text">订阅</span>
        </RouterLink>
        <RouterLink to="/tasks" class="nav-item" active-class="active">
          <span class="nav-text">任务</span>
        </RouterLink>
        <RouterLink to="/about" class="nav-item" active-class="active">
          <span class="nav-text">关于</span>
        </RouterLink>
      </nav>

      <!-- 移动端菜单按钮 -->
      <button
        class="mobile-menu-btn"
        @click="toggleMobileMenu"
        :class="{ 'active': isMobileMenuOpen }"
      >
        <span class="menu-line"></span>
        <span class="menu-line"></span>
        <span class="menu-line"></span>
      </button>
    </div>

    <!-- 移动端菜单 -->
    <div class="mobile-menu" :class="{ 'open': isMobileMenuOpen }">
      <RouterLink to="/" class="mobile-nav-item" @click="closeMobileMenu">
        首页
      </RouterLink>
      <RouterLink to="/library" class="mobile-nav-item" @click="closeMobileMenu">
        资源库
      </RouterLink>
      <RouterLink to="/subscription" class="mobile-nav-item" @click="closeMobileMenu">
        我的订阅
      </RouterLink>
      <RouterLink to="/tasks" class="mobile-nav-item" @click="closeMobileMenu">
        任务
      </RouterLink>
      <RouterLink to="/about" class="mobile-nav-item" @click="closeMobileMenu">
        关于
      </RouterLink>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

// 移动端菜单状态
const isMobileMenuOpen = ref(false)

// 切换移动端菜单
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// 关闭移动端菜单
const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

/* 品牌标识 */
.brand {
  flex-shrink: 0;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: inherit;
  transition: opacity 0.3s ease;
}

.brand-link:hover {
  opacity: 0.9;
}

.brand-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.brand-icon:hover {
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px) scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  transition: all var(--transition-normal);
}

.logo:hover {
  transform: scale(1.1);
  filter: brightness(1.1) contrast(1.1);
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.brand-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  line-height: 1;
}

.brand-subtitle {
  font-size: 0.75rem;
  opacity: 0.8;
  line-height: 1;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-item {
  text-decoration: none;
  color: inherit;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: white;
  border-radius: 1px;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  transition: transform 0.3s ease;
}

.menu-line {
  width: 24px;
  height: 2px;
  background: white;
  border-radius: 1px;
  transition: all 0.3s ease;
}

.mobile-menu-btn.active .menu-line:nth-child(1) {
  transform: rotate(45deg) translate(6px, 6px);
}

.mobile-menu-btn.active .menu-line:nth-child(2) {
  opacity: 0;
}

.mobile-menu-btn.active .menu-line:nth-child(3) {
  transform: rotate(-45deg) translate(6px, -6px);
}

/* 移动端菜单 */
.mobile-menu {
  display: none;
  background: rgba(102, 126, 234, 0.95);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-menu.open {
  display: block;
}

.mobile-nav-item {
  display: block;
  color: white;
  text-decoration: none;
  padding: 0.75rem 0;
  font-weight: 500;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: opacity 0.3s ease;
}

.mobile-nav-item:last-child {
  border-bottom: none;
}

.mobile-nav-item:hover {
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-container {
    padding: 0 1rem;
    height: 65px;
  }

  .brand-title {
    font-size: 1.25rem;
  }

  .brand-subtitle {
    font-size: 0.7rem;
  }

  .nav-menu {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
  }
}

@media (max-width: 480px) {
  .brand-icon {
    width: 36px;
    height: 36px;
  }

  .logo {
    width: 20px;
    height: 20px;
  }

  .brand-title {
    font-size: 1.1rem;
  }
}
</style>
