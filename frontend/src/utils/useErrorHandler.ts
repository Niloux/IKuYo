import { useFeedbackStore } from '../stores/feedbackStore'

/**
 * 统一错误处理composable
 * 提供标准化的错误处理方法，保持现有业务逻辑不变
 */
export const useErrorHandler = () => {
    const feedbackStore = useFeedbackStore()

    /**
     * 处理API错误（显示错误弹窗）
     * @param error 错误对象或字符串
     * @param context 错误上下文（可选）
     */
    const handleApiError = (error: unknown, context?: string) => {
        let message = '操作失败，请重试'

        if (error instanceof Error) {
            message = error.message
        } else if (typeof error === 'string') {
            message = error
        }

        const finalMessage = context ? `${context}: ${message}` : message
        feedbackStore.showError(finalMessage)
    }

    /**
     * 显示成功消息（Toast）
     * @param message 成功消息
     * @param context 操作上下文（可选）
     */
    const showSuccess = (message: string, context?: string) => {
        const finalMessage = context ? `${context}: ${message}` : message
        feedbackStore.showToast(finalMessage, 'success')
    }

    /**
     * 显示信息消息（Toast）
     * @param message 信息消息
     * @param context 操作上下文（可选）
     */
    const showInfo = (message: string, context?: string) => {
        const finalMessage = context ? `${context}: ${message}` : message
        feedbackStore.showToast(finalMessage, 'info')
    }

    /**
     * 处理表单验证错误
     * @param errors 验证错误对象
     * @param context 表单上下文（可选）
     */
    const handleValidationErrors = (errors: Record<string, string>, context?: string) => {
        const firstError = Object.values(errors)[0]
        if (firstError) {
            const finalMessage = context ? `${context}: ${firstError}` : firstError
            feedbackStore.showError(finalMessage)
        }
    }

    /**
     * 处理网络错误
     * @param error 网络错误
     * @param context 操作上下文（可选）
     */
    const handleNetworkError = (error: unknown, context?: string) => {
        let message = '网络连接失败，请检查网络后重试'

        // 根据错误类型提供更具体的消息
        if (error && typeof error === 'object' && 'code' in error) {
            switch ((error as any).code) {
                case 'NETWORK_ERROR':
                    message = '网络连接失败'
                    break
                case 'TIMEOUT':
                    message = '请求超时，请重试'
                    break
                case 'ABORT':
                    message = '请求被取消'
                    break
            }
        }

        const finalMessage = context ? `${context}: ${message}` : message
        feedbackStore.showError(finalMessage)
    }

    return {
        handleApiError,
        showSuccess,
        showInfo,
        handleValidationErrors,
        handleNetworkError
    }
}

/**
 * 错误类型枚举
 */
export const ErrorTypes = {
    API: 'api',
    NETWORK: 'network',
    VALIDATION: 'validation',
    PERMISSION: 'permission',
    NOT_FOUND: 'not_found'
} as const

export type ErrorType = typeof ErrorTypes[keyof typeof ErrorTypes]
