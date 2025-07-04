// 通用异步状态管理辅助函数
// 用法：const { loading, error, data, run } = useAsyncAction(asyncFn)
// run(...args) 执行异步请求，自动管理loading/error/data
import { ref } from 'vue'

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
