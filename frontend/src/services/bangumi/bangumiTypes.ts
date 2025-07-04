// =============================================================================
// Bangumi Types
// =============================================================================

import type { ApiResponse } from '../common/common';

// Bangumi领域类型定义
export interface BangumiCalendarItem {
    id: number;
    url: string;
    type: number;
    name: string;
    name_cn: string;
    summary: string;
    air_date: string;
    air_weekday: number;
    rating: {
        total: number;
        count: Record<string, number>;
        score: number;
    };
    rank: number;
    images: {
        large: string;
        common: string;
        medium: string;
        small: string;
        grid: string;
    };
}

export interface BangumiSubject {
    id: number;
    name: string;
    name_cn: string;
    summary: string;
    date: string;
    air_weekday: number;
    eps: number;
    total_episodes: number;
    rating: {
        total: number;
        count: Record<string, number>;
        score: number;
    };
    rank: number;
    images: {
        large: string;
        common: string;
        medium: string;
        small: string;
        grid: string;
    };
    collection: {
        wish: number;
        collect: number;
        doing: number;
        on_hold: number;
        dropped: number;
    };
    tags: { name: string; count: number; total_cont: number }[];
}

export interface BangumiWeekday {
    weekday: { en: string; cn: string; ja: string; id: number; };
    items: BangumiCalendarItem[];
}

export interface BangumiTag {
    name: string;
    count: number;
    total_cont: number;
}

// 集数可用性相关类型定义
export interface EpisodeAvailabilityData {
    bangumi_id: number;
    episodes: Record<string, {
        available: boolean;
        resource_count: number;
    }
    >;
}

// Bangumi章节相关类型定义
export interface BangumiEpisode {
    id: number;
    type: number;  // 0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 6:其他
    name: string;
    name_cn: string;
    sort: number;
    ep?: number;
    airdate?: string;
    comment: number;
    duration: string;
    desc: string;
    disc: number;
    duration_seconds?: number;
}

export interface BangumiEpisodesData {
    data: BangumiEpisode[];
    total: number;
}

// 后端章节API响应格式
export interface BangumiEpisodesResponse extends ApiResponse<BangumiEpisode[]> {
    total: number;  // 实际后端如有total字段则保留，否则可省略
}

// 资源相关类型定义
export interface SubtitleGroupResource {
    id: number;
    name: string;
    resource_count: number;
    resources: EpisodeResource[];
}

export interface EpisodeResource {
    id: number;
    episode_number: number;
    title: string;
    resolution: string;
    subtitle_type: string;
    magnet_url: string;
    torrent_url: string;
    release_date: string;
    size: string;
    group_id: number;
    group_name: string;
}

export interface EpisodeResourcesData {
    total_resources: number;
    subtitle_groups: SubtitleGroupResource[];
}
