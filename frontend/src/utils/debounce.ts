/**
 * 防抖函数
 * @param func 要防抖的函数
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: number | null = null

  return (...args: Parameters<T>) => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      func(...args)
      timeoutId = null
    }, delay) as unknown as number
  }
}

/**
 * 批量操作防抖器
 * 用于将多个快速操作合并为一次执行
 */
export class BatchDebouncer {
  private timeoutId: number | null = null
  private pendingOperations: (() => void)[] = []

  constructor(private delay: number = 300) {}

  /**
   * 添加待执行的操作
   * @param operation 操作函数
   */
  add(operation: () => void) {
    this.pendingOperations.push(operation)
    this.scheduleExecution()
  }

  private scheduleExecution() {
    if (this.timeoutId !== null) {
      clearTimeout(this.timeoutId)
    }

    this.timeoutId = setTimeout(() => {
      this.executePendingOperations()
    }, this.delay) as unknown as number
  }

  private executePendingOperations() {
    if (this.pendingOperations.length > 0) {

      this.pendingOperations.forEach(op => op())
      this.pendingOperations = []
    }
    this.timeoutId = null
  }

  /**
   * 立即执行所有待定操作
   */
  flush() {
    if (this.timeoutId !== null) {
      clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
    this.executePendingOperations()
  }
}

/**
 * 节流函数
 * @param func 要节流的函数
 * @param delay 节流间隔（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0
  let timeoutId: number | null = null

  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      func(...args)
    } else if (!timeoutId) {
      timeoutId = setTimeout(() => {
        lastCall = Date.now()
        func(...args)
        timeoutId = null
      }, delay - (now - lastCall)) as unknown as number
    }
  }
}
