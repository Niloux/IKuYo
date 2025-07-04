import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAsyncAction } from './asyncUtils'
import ScheduledJobApiService from '../services/scheduler/schedulerApiService'
import type { ScheduledJobCreate, ScheduledJobResponse, ScheduledJobUpdate } from '../services/scheduler/schedulerTypes'

/**
 * Pinia 定时任务管理 Store
 * 管理定时任务相关状态和异步操作
 */
export const useSchedulerStore = defineStore('scheduler', () => {
    const scheduledJobs = ref<ScheduledJobResponse[]>([])

    // 获取所有计划任务列表
    const fetchScheduledJobsAsync = useAsyncAction(() => ScheduledJobApiService.listScheduledJobs())
    /**
     * 获取所有计划任务列表
     * @returns Promise<ScheduledJobResponse[]>
     */
    const fetchScheduledJobs = async () => {
        const result = await fetchScheduledJobsAsync.run()
        scheduledJobs.value = result
        return result
    }

    // 创建新的计划任务
    const createScheduledJobAsync = useAsyncAction((jobCreateData: ScheduledJobCreate) => ScheduledJobApiService.createScheduledJob(jobCreateData))
    /**
     * 创建新的计划任务
     * @param jobCreateData 计划任务创建数据
     * @returns Promise<ScheduledJobResponse>
     */
    const createScheduledJob = async (jobCreateData: ScheduledJobCreate) => {
        const result = await createScheduledJobAsync.run(jobCreateData)
        await fetchScheduledJobs()
        return result
    }

    // 更新计划任务
    const updateScheduledJobAsync = useAsyncAction((job_id: string, jobUpdateData: ScheduledJobUpdate) => ScheduledJobApiService.updateScheduledJob(job_id, jobUpdateData))
    const updateScheduledJob = async (job_id: string, jobUpdateData: ScheduledJobUpdate) => {
        const result = await updateScheduledJobAsync.run(job_id, jobUpdateData)
        await fetchScheduledJobs()
        return result
    }

    // 删除计划任务
    const deleteScheduledJobAsync = useAsyncAction((job_id: string) => ScheduledJobApiService.deleteScheduledJob(job_id))
    const deleteScheduledJob = async (job_id: string) => {
        const result = await deleteScheduledJobAsync.run(job_id)
        await fetchScheduledJobs()
        return result
    }

    // 切换计划任务启用/禁用状态
    const toggleScheduledJobAsync = useAsyncAction((job_id: string) => ScheduledJobApiService.toggleScheduledJob(job_id))
    const toggleScheduledJob = async (job_id: string) => {
        const result = await toggleScheduledJobAsync.run(job_id)
        await fetchScheduledJobs()
        return result
    }

    return {
        scheduledJobs,
        fetchScheduledJobs, createScheduledJob, updateScheduledJob, deleteScheduledJob, toggleScheduledJob,
        fetchScheduledJobsAsync, createScheduledJobAsync, updateScheduledJobAsync, deleteScheduledJobAsync, toggleScheduledJobAsync
    }
})
