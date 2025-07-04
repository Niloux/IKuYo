import { defineStore } from 'pinia';

export type ToastType = 'success' | 'error' | 'info';
export interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

export const useFeedbackStore = defineStore('feedback', {
    state: () => ({
        loading: false as boolean,
        toasts: [] as Toast[],
        error: '' as string | null,
        toastId: 0 as number,
    }),
    actions: {
        showLoading() {
            this.loading = true;
        },
        hideLoading() {
            this.loading = false;
        },
        showToast(message: string, type: ToastType = 'info', duration = 2500) {
            const id = ++this.toastId;
            this.toasts.push({ id, message, type });
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, duration);
        },
        showError(message: string) {
            this.error = message;
        },
        clearError() {
            this.error = '';
        },
    },
});
