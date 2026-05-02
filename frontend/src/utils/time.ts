/**
 * 将 ISO 8601 时间字符串转为简短中文相对时间（如「3 分钟前」「2 天前」）。
 */
export function formatRelativeTime(iso: string): string {
  if (!iso?.trim()) return ''
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return ''
  const diff = Date.now() - t
  if (diff < 0) return '刚刚'
  const sec = Math.floor(diff / 1000)
  const min = Math.floor(sec / 60)
  const hr = Math.floor(min / 60)
  const day = Math.floor(hr / 24)
  if (day >= 30) return `${Math.floor(day / 30)}个月前`
  if (day >= 1) return `${day}天前`
  if (hr >= 1) return `${hr}小时前`
  if (min >= 1) return `${min}分钟前`
  return '刚刚'
}
