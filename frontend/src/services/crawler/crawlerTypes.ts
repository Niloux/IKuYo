// =============================================================================
// Crawler Types
// =============================================================================

export interface CrawlerTaskCreate {
    mode: 'homepage' | 'season' | 'year';
    year?: number;
    season?: '春' | '夏' | '秋' | '冬';
    limit?: number;
}

// 爬虫任务相关类型
export interface TaskResponse {
    id: number;
    task_type: string;
    status: string;
    parameters?: string;
    result_summary?: string;
    created_at?: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    percentage?: number;
    processed_items?: number;
    total_items?: number;
    processing_speed?: number;
    estimated_remaining?: number;
}
