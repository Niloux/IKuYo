/**
 * 滚动管理工具函数
 */

/**
 * 确保页面滚动到顶部（优化版）
 * @param immediate 是否立即执行，默认true
 */
export const ensureScrollToTop = (immediate: boolean = true) => {
  const scrollToTop = () => {
    if (window.scrollY > 0) {
      window.scrollTo({ top: 0, behavior: 'instant' })
    }
  }

  if (immediate) {
    scrollToTop()
  }

  // 使用requestAnimationFrame确保DOM更新后执行
  requestAnimationFrame(() => {
    scrollToTop()
  })
}

/**
 * 恢复滚动位置（优化版）
 * @param position 目标滚动位置
 */
export const restoreScrollPosition = (position: number) => {
  if (position > 0) {
    requestAnimationFrame(() => {
      window.scrollTo({ top: position, behavior: 'instant' })
    })
  }
}

/**
 * 获取当前滚动位置
 */
export const getCurrentScrollPosition = (): number => {
  return window.scrollY
}

/**
 * 平滑滚动到顶部（用于置顶按钮）
 */
export const smoothScrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}
