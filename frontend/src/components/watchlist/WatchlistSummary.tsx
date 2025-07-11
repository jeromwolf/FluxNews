'use client'

import { 
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  NewspaperIcon,
  SparklesIcon,
  BellIcon
} from '@heroicons/react/24/outline'

interface WatchlistSummaryProps {
  watchlist: Array<{
    priceChangeType: 'up' | 'down'
    priceChange: string
    impactScore: number
    recentNewsCount: number
    alerts: {
      priceAlert: boolean
      newsAlert: boolean
      impactAlert: boolean
    }
  }>
}

export default function WatchlistSummary({ watchlist }: WatchlistSummaryProps) {
  // 통계 계산
  const totalCompanies = watchlist.length
  const risingCompanies = watchlist.filter(w => w.priceChangeType === 'up').length
  const fallingCompanies = watchlist.filter(w => w.priceChangeType === 'down').length
  const avgImpactScore = watchlist.reduce((sum, w) => sum + w.impactScore, 0) / totalCompanies || 0
  const totalNews = watchlist.reduce((sum, w) => sum + w.recentNewsCount, 0)
  const activeAlerts = watchlist.filter(w => 
    w.alerts.priceAlert || w.alerts.newsAlert || w.alerts.impactAlert
  ).length

  const stats = [
    {
      name: '전체 기업',
      value: totalCompanies,
      icon: ChartBarIcon,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100 dark:bg-gray-800'
    },
    {
      name: '상승',
      value: risingCompanies,
      icon: ArrowTrendingUpIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      percentage: totalCompanies > 0 ? `${((risingCompanies / totalCompanies) * 100).toFixed(0)}%` : '0%'
    },
    {
      name: '하락',
      value: fallingCompanies,
      icon: ArrowTrendingDownIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-100 dark:bg-red-900/20',
      percentage: totalCompanies > 0 ? `${((fallingCompanies / totalCompanies) * 100).toFixed(0)}%` : '0%'
    },
    {
      name: '평균 영향도',
      value: `${(avgImpactScore * 100).toFixed(0)}%`,
      icon: SparklesIcon,
      color: 'text-electric-blue',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20'
    },
    {
      name: '총 뉴스',
      value: totalNews,
      icon: NewspaperIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20'
    },
    {
      name: '활성 알림',
      value: activeAlerts,
      icon: BellIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20'
    }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.name}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-4"
        >
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${stat.bgColor}`}>
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stat.name}
              </p>
              <div className="flex items-baseline">
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
                {stat.percentage && (
                  <span className="ml-1 text-xs text-gray-500 dark:text-gray-400">
                    ({stat.percentage})
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}