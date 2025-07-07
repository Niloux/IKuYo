// 全局交互反馈Store：统一管理全局loading、toast、error状态
// 用于全局Loading遮罩、全局消息提示（Toast）、全局错误弹窗（Error）
// 通过Pinia store实现，所有页面和组件均可直接调用
import { defineStore } from 'pinia';

export type ToastType = 'success' | 'error' | 'info';
export interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

export const useFeedbackStore = defineStore('feedback', {
    state: () => ({
        loading: false as boolean, // 全局Loading遮罩状态
        toast: null as Toast | null,     // 当前全局Toast消息（只保留一条）
        error: '' as string | null, // 全局Error弹窗内容
        toastId: 0 as number,
        toastTimer: null as ReturnType<typeof setTimeout> | null, // 新增：toast定时器
        // 延迟loading定时器
        _loadingTimer: null as ReturnType<typeof setTimeout> | null,
    }),
    actions: {
        // 显示全局Loading遮罩（延迟150ms）
        showLoading() {
            if (this._loadingTimer) return;
            this._loadingTimer = setTimeout(() => {
                this.loading = true;
                this._loadingTimer = null;
            }, 150);
        },
        // 隐藏全局Loading遮罩
        hideLoading() {
            if (this._loadingTimer) {
                clearTimeout(this._loadingTimer);
                this._loadingTimer = null;
            }
            this.loading = false;
        },
        // 推送全局Toast消息（只保留一条）
        showToast(message: string, type: ToastType = 'info', duration = 2500) {
            const id = ++this.toastId;
            // 清除旧定时器
            if (this.toastTimer) {
                clearTimeout(this.toastTimer);
                this.toastTimer = null;
            }
            this.toast = { id, message, type };
            this.toastTimer = setTimeout(() => {
                this.toast = null;
                this.toastTimer = null;
            }, duration);
        },
        // 手动关闭Toast
        closeToast() {
            if (this.toastTimer) {
                clearTimeout(this.toastTimer);
                this.toastTimer = null;
            }
            this.toast = null;
        },
        // 显示全局Error弹窗
        showError(message: string) {
            this.error = message;
        },
        // 清除全局Error弹窗
        clearError() {
            this.error = '';
        },
    },
});
