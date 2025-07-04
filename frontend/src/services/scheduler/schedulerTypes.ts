// =============================================================================
// Scheduler Types
// =============================================================================

export interface ScheduledJobCreate {
    job_id: string;
    name: string;
    cron_expression: string;
    parameters: Record<string, any>;
    enabled?: boolean;
    description?: string;
}

export interface ScheduledJobUpdate {
    name?: string;
    cron_expression?: string;
    parameters?: Record<string, any>;
    enabled?: boolean;
    description?: string;
}

export interface ScheduledJobResponse {
    id?: number;
    job_id: string;
    name: string;
    cron_expression: string;
    parameters: Record<string, any>;
    enabled: boolean;
    description?: string;
    created_at?: string;
    updated_at?: string;
}
