// 通用异步状态管理辅助函数
// 用法：const { loading, error, data, run } = useAsyncAction(asyncFn)
// run(...args) 执行异步请求，自动管理loading/error/data
import { ref } from 'vue'

/**
 * 通用异步状态管理辅助函数
 * @template T 异步函数类型
 * @param asyncFn 需要包装的异步函数（返回Promise）
 * @returns { loading, error, data, run } 统一的异步状态对象和执行方法
 * @example
 * const { loading, error, data, run } = useAsyncAction(fetchData)
 * await run(...args)
 */
export function useAsyncAction<T extends (...args: any[]) => Promise<any>>(asyncFn: T) {
    const loading = ref(false)
    const error = ref<string | null>(null)
    const data = ref<any>(null)

    const run = async (...args: Parameters<T>) => {
        loading.value = true
        error.value = null
        data.value = null
        try {
            const result = await asyncFn(...args)
            data.value = result
            return result
        } catch (err: any) {
            error.value = err?.message || '请求失败'
            throw err
        } finally {
            loading.value = false
        }
    }

    return { loading, error, data, run }
}
