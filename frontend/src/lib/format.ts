import { useLocale } from 'next-intl'

export function formatDate(date: Date | string, locale: string, format: 'short' | 'medium' | 'long' = 'medium'): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  switch (format) {
    case 'short':
      return new Intl.DateTimeFormat(locale, {
        month: '2-digit',
        day: '2-digit'
      }).format(dateObj)
    
    case 'medium':
      if (locale === 'ko') {
        return new Intl.DateTimeFormat(locale, {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }).format(dateObj)
      }
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }).format(dateObj)
    
    case 'long':
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: locale === 'ko' ? 'long' : 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(dateObj)
  }
}

export function formatCurrency(amount: number, locale: string, currency: 'KRW' | 'USD' = 'KRW'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

export function formatNumber(value: number, locale: string, compact = false): string {
  if (compact) {
    const formatter = new Intl.NumberFormat(locale, {
      notation: 'compact',
      compactDisplay: 'short',
      maximumFractionDigits: 1
    })
    return formatter.format(value)
  }
  
  return new Intl.NumberFormat(locale).format(value)
}

export function formatPercentage(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1
  }).format(value / 100)
}

export function formatRelativeTime(date: Date | string, locale: string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)
  
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
  
  if (diffInSeconds < 60) {
    return rtf.format(-diffInSeconds, 'second')
  } else if (diffInSeconds < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), 'minute')
  } else if (diffInSeconds < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour')
  } else if (diffInSeconds < 2592000) {
    return rtf.format(-Math.floor(diffInSeconds / 86400), 'day')
  } else {
    return formatDate(dateObj, locale, 'medium')
  }
}

// Custom hook for formatting
export function useFormatter() {
  const locale = useLocale()
  
  return {
    formatDate: (date: Date | string, format?: 'short' | 'medium' | 'long') => 
      formatDate(date, locale, format),
    formatCurrency: (amount: number, currency?: 'KRW' | 'USD') => 
      formatCurrency(amount, locale, currency),
    formatNumber: (value: number, compact?: boolean) => 
      formatNumber(value, locale, compact),
    formatPercentage: (value: number) => 
      formatPercentage(value, locale),
    formatRelativeTime: (date: Date | string) => 
      formatRelativeTime(date, locale)
  }
}