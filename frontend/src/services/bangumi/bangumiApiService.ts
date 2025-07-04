// =============================================================================
// Bangumi API Service
// =============================================================================

import { apiClient } from '../common/common';
import type { ApiResponse } from '../common/common';
import type { BangumiCalendarItem, BangumiSubject, BangumiWeekday, EpisodeAvailabilityData, BangumiEpisodesData, BangumiEpisode, EpisodeResourcesData } from './bangumiTypes';

/**
 * 数据转换工具：BangumiSubject 转换为 BangumiCalendarItem
 */
export function convertSubjectToCalendarItem(subject: BangumiSubject):
    BangumiCalendarItem {
    return {
        id: subject.id,
        url: `https://bgm.tv/subject/${subject.id}`,
        type: 2,  // 动画类型
        name: subject.name,
        name_cn: subject.name_cn,
        summary: subject.summary,
        air_date: subject.date,
        air_weekday: subject.air_weekday,
        rating: subject.rating,
        rank: subject.rank,
        images: subject.images
    };
}

// API服务类
export class BangumiApiService {
    /**
     * 获取每日放送
     */
    static async getCalendar(): Promise<BangumiWeekday[]> {
        const response: ApiResponse<BangumiWeekday[]> =
            await apiClient.get('/animes/calendar')
        return response.data
    }

    /**
     * 获取番剧详情
     */
    static async getSubject(bangumiId: number): Promise<BangumiSubject> {
        const response: ApiResponse<BangumiSubject> =
            await apiClient.get(`/animes/${bangumiId}`)
        return response.data
    }

    /**
     * 获取集数可用性状态
     */
    static async getEpisodeAvailability(bangumiId: number):
        Promise<EpisodeAvailabilityData> {
        const response: ApiResponse<EpisodeAvailabilityData> =
            await apiClient.get(`/animes/${bangumiId}/episodes/availability`)
        return response.data
    }

    /**
     * 获取Bangumi章节信息
     */
    static async getBangumiEpisodes(
        subjectId: number, episodeType?: number, limit: number = 100,
        offset: number = 0): Promise<BangumiEpisodesData> {
        const params: Record<string, any> = { limit, offset };
        if (episodeType !== undefined) {
            params.episode_type = episodeType;
        }

        const response: ApiResponse<BangumiEpisode[]> =
            await apiClient.get(`/animes/${subjectId}/episodes`, { params });

        // 若total为通用字段，直接返回
        return { data: response.data, total: response.total ?? 0 };
    }

    /**
     * 获取特定集数的资源列表
     */
    static async getEpisodeResources(bangumiId: number, episode: number):
        Promise<EpisodeResourcesData> {
        const response: ApiResponse<EpisodeResourcesData> = await apiClient.get(
            `/animes/${bangumiId}/resources?episode=${episode}`);
        return response.data;
    }

    /**
     * 获取番剧的所有资源列表
     */
    static async getAnimeResources(bangumiId: number, options?: {
        resolution?: string,
        subtitle_type?: string,
        limit?: number,
        offset?: number
    }): Promise<EpisodeResourcesData> {
        const params: Record<string, any> = {};

        if (options?.resolution) params.resolution = options.resolution;
        if (options?.subtitle_type) params.subtitle_type = options.subtitle_type;
        if (options?.limit) params.limit = options.limit;
        if (options?.offset) params.offset = options.offset;

        const response: ApiResponse<EpisodeResourcesData> =
            await apiClient.get(`/animes/${bangumiId}/resources`, { params });
        return response.data;
    }

    /**
     * 资源库搜索
     */
    static async searchLibrary(
        query: string, page: number = 1, limit: number = 12): Promise<
            {
                bangumi_ids: number[]
                pagination: {
                    current_page: number
                    per_page: number
                    total: number
                    total_pages: number
                    has_next: boolean
                    has_prev: boolean
                }
            }> {
        const response: ApiResponse<{
            bangumi_ids: number[]
            pagination: any
        }> = await apiClient.get('/animes/search', {
            params: { q: query, page, limit }
        });
        return response.data;
    }

    /**
     * 批量获取番剧详情
     */
    static async batchGetSubjects(bangumiIds: number[]): Promise<{
        success: BangumiSubject[]; failed: { id: number; reason: any }[];
    }> {
        const promises = bangumiIds.map(
            id => this.getSubject(id).then(
                value => ({ status: 'fulfilled', value, id } as const),
                reason => ({ status: 'rejected', reason, id } as const)));
        const results = await Promise.all(promises);
        const success: BangumiSubject[] = [];
        const failed: { id: number; reason: any }[] = [];
        for (const r of results) {
            if (r.status === 'fulfilled')
                success.push(r.value);
            else if (r.status === 'rejected')
                failed.push({ id: r.id, reason: r.reason });
        }
        return { success, failed };
    }
}

export default BangumiApiService;
