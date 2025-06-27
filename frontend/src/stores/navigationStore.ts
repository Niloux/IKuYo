import { defineStore } from 'pinia'

const NAVIGATION_KEY = 'ikuyo_navigation_state'

export const useNavigationStore = defineStore('navigation', () => {
  
  // 记录详情页访问（在从列表页跳转到详情页时调用）
  const recordDetailPageVisit = (detailPath: string, fromPath?: string) => {
    try {
      // 尝试从document.referrer获取来源，或使用传入的fromPath
      const sourcePath = fromPath || document.referrer.split(window.location.origin)[1] || ''
      
      const navigationData = {
        lastDetailPath: detailPath,
        timestamp: Date.now(),
        fromPath: sourcePath
      }
      sessionStorage.setItem(NAVIGATION_KEY, JSON.stringify(navigationData))
      console.log(`记录详情页访问: ${detailPath} 来自 ${sourcePath}`)
    } catch (err) {
      console.error('记录导航状态失败:', err)
    }
  }
  
  // 检查是否从详情页返回到指定页面（增强版）
  const isReturningFromDetail = (targetPath: string): boolean => {
    const referrer = document.referrer
    const currentPath = window.location.pathname
    
    // 检查当前路径是否匹配目标路径
    const isTargetPath = currentPath === targetPath || currentPath.startsWith(targetPath)
    
    // 方法1: 基于referrer检测
    const isFromDetailByReferrer = referrer.includes('/anime/') || referrer.includes('/library/detail/')
    
         // 方法2: 基于sessionStorage检测
     let isFromDetailByStorage = false
     try {
       const saved = sessionStorage.getItem(NAVIGATION_KEY)
       if (saved) {
         const navigationData = JSON.parse(saved)
         // 导航记录在整个会话期间有效，不设置时间限制
         // 因为用户可能在详情页停留很长时间，比如仔细查看番剧信息
         const isRecent = true
         const isDetailPath = navigationData.lastDetailPath && (
           navigationData.lastDetailPath.includes('/anime/') || 
           navigationData.lastDetailPath.includes('/library/detail/')
         )
         const isCorrectReturnPath = navigationData.fromPath === targetPath || 
                                    navigationData.fromPath.startsWith(targetPath)
         
         isFromDetailByStorage = isRecent && isDetailPath && isCorrectReturnPath
         
         console.log(`sessionStorage检测结果:`, {
           navigationData,
           isRecent,
           isDetailPath,
           isCorrectReturnPath,
           isFromDetailByStorage
         })
       }
     } catch (err) {
       console.error('读取导航状态失败:', err)
     }
    
    const result = isTargetPath && (isFromDetailByReferrer || isFromDetailByStorage)
    
    console.log(`检查从详情页返回 ${targetPath}:`, {
      referrer,
      currentPath,
      isTargetPath,
      isFromDetailByReferrer,
      isFromDetailByStorage,
      result
    })
    
    // 如果检测到返回，清除导航记录避免重复使用
    if (result) {
      try {
        sessionStorage.removeItem(NAVIGATION_KEY)
        console.log('已清除导航记录')
      } catch (err) {
        console.error('清除导航记录失败:', err)
      }
    }
    
    return result
  }
  
  return {
    isReturningFromDetail,
    recordDetailPageVisit
  }
}) 