// 任务相关工具函数

export function getParameter(parameters: string | undefined, key: string): string {
  if (!parameters) return '-'
  try {
    const params = JSON.parse(parameters)
    // 特殊处理mode字段，显示更友好的信息
    if (key === 'mode') {
      const mode = params.mode || '-';
      switch (mode) {
        case 'homepage':
          return '首页';
        case 'season':
          return `季度 (${params.year || ''}年${params.season || ''})`;
        case 'year':
          return `年份 (${params.year || ''}年)`;
        default:
          return mode;
      }
    }
    return params[key] || '-'
  } catch (e) {
    console.error('解析参数失败:', e)
    return '-'
  }
}

export function formatDateTime(dateTimeStr: string | undefined): string {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString()
}

export function formatTime(seconds: number | undefined): string {
  if (seconds === undefined || seconds < 0) return '-'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}
