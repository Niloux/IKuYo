// 任务相关工具函数

export function getParameter(parameters: string | undefined, key: string): string {
  if (!parameters) return '-'
  try {
    const params = JSON.parse(parameters)
    if (key === 'mode' && params.bangumi_id) {
      return `bangumi_id: ${params.bangumi_id}`
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
