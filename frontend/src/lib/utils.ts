import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 全站日期時間格式統一：2026/07/02 13:00（24 小時制、不用上午/下午，避免中文 locale 預設格式跳來跳去）
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}

// 空間有限的地方用（新聞列表），省年份：07/02 13:00
export function formatTimeShort(iso: string): string {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}

// 純日期／月份字串（已經是 "2026-06-26"／"2026-06" 這種零填充格式），統一分隔符號成 "/"
export function formatDate(dateStr: string): string {
  return dateStr.replaceAll("-", "/")
}
