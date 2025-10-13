import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format phone number to Kenya standard
 */
export function formatPhoneNumber(phone: string): string {
  // Remove all non-numeric characters
  const cleaned = phone.replace(/\D/g, '')
  
  // Handle different formats
  if (cleaned.startsWith('254')) {
    return '+' + cleaned
  } else if (cleaned.startsWith('0')) {
    return '+254' + cleaned.slice(1)
  } else if (cleaned.length === 9) {
    return '+254' + cleaned
  }
  
  return '+' + cleaned
}

/**
 * Validate Kenya phone number
 */
export function isValidKenyaPhone(phone: string): boolean {
  const cleaned = phone.replace(/\D/g, '')
  
  // Kenya numbers: 254XXXXXXXXX (12 digits) or 0XXXXXXXXX (10 digits)
  if (cleaned.startsWith('254') && cleaned.length === 12) {
    return true
  }
  if (cleaned.startsWith('0') && cleaned.length === 10) {
    return true
  }
  if (cleaned.length === 9) {
    return true
  }
  
  return false
}

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
    second: 1
  }
  
  for (const [unit, secondsInUnit] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secondsInUnit)
    if (interval >= 1) {
      return `${interval} ${unit}${interval === 1 ? '' : 's'} ago`
    }
  }
  
  return 'Just now'
}

/**
 * Format date to readable string
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-KE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Get bloom risk color
 */
export function getBloomRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'high':
      return 'text-red-600 bg-red-50 dark:bg-red-950'
    case 'moderate':
      return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950'
    case 'low':
      return 'text-green-600 bg-green-50 dark:bg-green-950'
    default:
      return 'text-gray-600 bg-gray-50 dark:bg-gray-950'
  }
}

/**
 * Get health score color
 */
export function getHealthScoreColor(score: number): string {
  if (score >= 75) return 'text-green-600'
  if (score >= 50) return 'text-yellow-600'
  if (score >= 25) return 'text-orange-600'
  return 'text-red-600'
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Format region name (replace underscores with spaces, capitalize)
 */
export function formatRegionName(region: string): string {
  return region.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

/**
 * Generate random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15)
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }
    
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}

/**
 * Sleep utility for async operations
 */
export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * Check if running on server
 */
export const isServer = typeof window === 'undefined'

/**
 * Safe JSON parse
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json)
  } catch {
    return fallback
  }
}

