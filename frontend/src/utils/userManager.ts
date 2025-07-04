/**
 * 用户身份管理工具
 * 负责生成和管理用户UUID，用于订阅功能的用户识别
 */

export class UserManager {
    private static readonly USER_ID_KEY = 'ikuyo_user_id'

    /**
     * 获取当前用户ID，如果不存在则自动生成
     */
    static getUserId(): string {
        let userId = localStorage.getItem(this.USER_ID_KEY)
        if (!userId) {
            userId = this.generateUserId()
            localStorage.setItem(this.USER_ID_KEY, userId)
        }
        return userId
    }

    /**
 * 生成新的用户ID
 */
    private static generateUserId(): string {
        // 优先使用crypto.randomUUID()，如果不可用则使用备选方案
        if (typeof crypto !== 'undefined' && crypto.randomUUID) {
            try {
                return 'user_' + crypto.randomUUID()
            } catch (error) {
                console.warn('crypto.randomUUID() 不可用，使用备选方案生成UUID')
            }
        }

        // 备选方案：生成伪UUID
        return 'user_' + this.generateFallbackUUID()
    }

    /**
     * 备选UUID生成方法（兼容所有浏览器）
     */
    private static generateFallbackUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0
            const v = c === 'x' ? r : (r & 0x3 | 0x8)
            return v.toString(16)
        })
    }

    /**
     * 清除用户ID（用于测试或重置）
     */
    static clearUserId(): void {
        localStorage.removeItem(this.USER_ID_KEY)
    }

    /**
     * 检查是否已有用户ID
     */
    static hasUserId(): boolean {
        return localStorage.getItem(this.USER_ID_KEY) !== null
    }
}
