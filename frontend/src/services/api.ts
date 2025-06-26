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
    }

    // 导出axios实例供其他服务使用
    export {apiClient};
    export default BangumiApiService;