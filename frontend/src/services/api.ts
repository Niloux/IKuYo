import axios, {type AxiosResponse} from 'axios'

// API基础配置
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器 - 统一处理响应数据
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 直接返回data部分
    return response.data
  },
  (error) => {
    console.error('API请求失败:', error)
    return Promise.reject(error)
  }
)

    // 定义API响应类型
    export interface ApiResponse<T = any> {
      success: boolean
      message: string
      data: T
    }

    // Bangumi相关类型定义
    export interface BangumiCalendarItem {
      id: number
      url: string
      type: number
      name: string
      name_cn: string
      summary: string
      air_date: string
      air_weekday: number
      rating: {total: number
    count: Record<string, number>
    score: number
  }
  rank: number
    images: {large: string
    common: string
    medium: string
    small: string
    grid: string
  }
    }

    export interface BangumiWeekday {
      weekday: {en: string
      cn: string
      ja: string
    id: number
  }
  items: BangumiCalendarItem[]
    }

    export interface BangumiTag {
      name: string
      count: number
      total_cont: number
    }

    export interface BangumiSubject {
      id: number
      name: string
      name_cn: string
      summary: string
      date: string
      air_weekday: number
      eps: number
      rating: {total: number
    count: Record<string, number>
    score: number
  }
  rank: number
    images: {large: string
    common: string
    medium: string
    small: string
    grid: string
  }
  collection: {
    wish: number
    collect: number
    doing: number
    on_hold: number
    dropped: number
  }
  tags: BangumiTag[]
    }

    // 集数可用性相关类型定义
    export interface EpisodeAvailabilityData {
      bangumi_id: number
      episodes: Record < string, {available: boolean
    resource_count: number
  }>
    }

    // Bangumi章节相关类型定义
    export interface BangumiEpisode {
      id: number
      type: number  // 0:正片, 1:SP, 2:OP, 3:ED, 4:PV, 6:其他
      name: string
      name_cn: string
      sort: number
      ep?: number
      airdate?: string
      comment: number
      duration: string
      desc: string
      disc: number
      duration_seconds?: number
    }

    export interface BangumiEpisodesData {
      data: BangumiEpisode[]
      total: number
    }

    // 后端章节API响应格式
    export interface BangumiEpisodesResponse extends
        ApiResponse<BangumiEpisode[]> {
      total: number
    }

    export interface BangumiEpisodesStats {
      total: number
      main_episodes: number
      special_episodes: number
      opening_episodes: number
      ending_episodes: number
      pv_episodes: number
      other_episodes: number
    }

    // 资源相关类型定义
    export interface SubtitleGroupResource {
      id: number
      title: string
      resolution?: string
      subtitle_type?: string
      file_size?: string
      magnet_url?: string
      torrent_url?: string
      release_date?: string
    }

    export interface SubtitleGroupData {
      id: number
      name: string
      resource_count: number
      resources: SubtitleGroupResource[]
    }

    export interface EpisodeResourcesData {
      bangumi_id: number
      episode: number
      total_resources: number
      subtitle_groups: SubtitleGroupData[]
    }

    // API服务类
    export class BangumiApiService {
      /**
       * 获取每日放送
       */
      static async getCalendar(): Promise<BangumiWeekday[]> {
        const response: ApiResponse<BangumiWeekday[]> =
            await apiClient.get('/bangumi/calendar')
        return response.data
      }

      /**
       * 获取番剧详情
       */
      static async getSubject(bangumiId: number): Promise<BangumiSubject> {
        const response: ApiResponse<BangumiSubject> =
            await apiClient.get(`/bangumi/subjects/${bangumiId}`)
        return response.data
      }

      /**
       * 获取集数可用性状态
       */
      static async getEpisodeAvailability(bangumiId: number):
          Promise<EpisodeAvailabilityData> {
        const response: ApiResponse<EpisodeAvailabilityData> =
            await apiClient.get(
                `/animes/bangumi/${bangumiId}/episodes/availability`)
        return response.data
      }

      /**
       * 获取Bangumi章节信息
       */
      static async getBangumiEpisodes(
          subjectId: number, episodeType?: number, limit: number = 100,
          offset: number = 0): Promise<BangumiEpisodesData> {
        const params: Record<string, any> = {limit, offset};
        if (episodeType !== undefined) {
          params.episode_type = episodeType;
        }

        const response: BangumiEpisodesResponse = await apiClient.get(
            `/bangumi/subjects/${subjectId}/episodes`, {params});

        // 后端返回的是包装过的响应，需要提取实际数据
        return {data: response.data, total: response.total};
      }

      /**
       * 获取Bangumi章节统计信息
       */
      static async getBangumiEpisodesStats(subjectId: number):
          Promise<BangumiEpisodesStats> {
        const response: ApiResponse<BangumiEpisodesStats> = await apiClient.get(
            `/bangumi/subjects/${subjectId}/episodes/stats`);
        return response.data;
      }

      /**
       * 获取特定集数的资源列表
       */
      static async getEpisodeResources(bangumiId: number, episode: number):
          Promise<EpisodeResourcesData> {
        const response: ApiResponse<EpisodeResourcesData> = await apiClient.get(
            `/animes/bangumi/${bangumiId}/episodes/${episode}/resources`);
        return response.data;
      }
    }

    // 导出axios实例供其他服务使用
    export {apiClient};
    export default BangumiApiService;