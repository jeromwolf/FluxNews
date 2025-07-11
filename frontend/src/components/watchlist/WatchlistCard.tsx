'use client'

import { useState } from 'react'
import { 
  TrashIcon,
  ChartBarIcon,
  NewspaperIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  Cog6ToothIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { BellIcon as BellSolidIcon } from '@heroicons/react/24/solid'
import AlertSettingsModal from './AlertSettingsModal'

interface WatchlistCardProps {
  watchlistItem: {
    id: string
    companyId: string
    companyName: string
    category: string
    addedAt: string
    currentPrice: string
    priceChange: string
    priceChangeType: 'up' | 'down'
    marketCap: string
    impactScore: number
    recentNewsCount: number
    alerts: {
      priceAlert: boolean
      newsAlert: boolean
      impactAlert: boolean
      thresholds: {
        priceChange: number
        impactScore: number
      }
    }
    recentNews: Array<{
      title: string
      date: string
      sentiment: string
    }>
  }
  onRemove: (id: string) => void
  onUpdateAlerts: (id: string, alerts: {
    priceAlert: boolean
    newsAlert: boolean
    impactAlert: boolean
    thresholds: {
      priceChange: number
      impactScore: number
    }
  }) => void
  onViewDetails: (company: WatchlistCardProps['watchlistItem']) => void
}

export default function WatchlistCard({ 
  watchlistItem, 
  onRemove, 
  onUpdateAlerts,
  onViewDetails 
}: WatchlistCardProps) {
  const [showAlertSettings, setShowAlertSettings] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const hasActiveAlerts = watchlistItem.alerts.priceAlert || 
                         watchlistItem.alerts.newsAlert || 
                         watchlistItem.alerts.impactAlert

  const getImpactColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600 dark:text-red-400'
    if (score >= 0.6) return 'text-orange-600 dark:text-orange-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {watchlistItem.companyName}
                </h3>
                {hasActiveAlerts && (
                  <BellSolidIcon className="h-4 w-4 text-electric-blue ml-2" />
                )}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {watchlistItem.category} · {watchlistItem.marketCap}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowAlertSettings(true)}
                className="p-1.5 text-gray-400 hover:text-gray-500 transition-colors"
                title="알림 설정"
              >
                <Cog6ToothIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => onRemove(watchlistItem.id)}
                className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                title="삭제"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* 주가 정보 */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">현재가</span>
                <div className="flex items-center">
                  {watchlistItem.priceChangeType === 'up' ? (
                    <ArrowTrendingUpIcon className="h-4 w-4 text-green-600 mr-1" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-4 w-4 text-red-600 mr-1" />
                  )}
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {watchlistItem.currentPrice}
                  </span>
                </div>
              </div>
              <div className="mt-1 text-right">
                <span className={`text-sm font-medium ${
                  watchlistItem.priceChangeType === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {watchlistItem.priceChange}
                </span>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">영향도</span>
                <div className="flex items-center">
                  <SparklesIcon className={`h-4 w-4 mr-1 ${getImpactColor(watchlistItem.impactScore)}`} />
                  <span className={`font-semibold ${getImpactColor(watchlistItem.impactScore)}`}>
                    {(watchlistItem.impactScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="mt-1 text-right">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  뉴스 {watchlistItem.recentNewsCount}건
                </span>
              </div>
            </div>
          </div>

          {/* 알림 상태 */}
          <div className="flex items-center space-x-4 mb-4 text-sm">
            <div className={`flex items-center ${
              watchlistItem.alerts.priceAlert ? 'text-electric-blue' : 'text-gray-400'
            }`}>
              <ChartBarIcon className="h-4 w-4 mr-1" />
              <span>가격</span>
            </div>
            <div className={`flex items-center ${
              watchlistItem.alerts.newsAlert ? 'text-electric-blue' : 'text-gray-400'
            }`}>
              <NewspaperIcon className="h-4 w-4 mr-1" />
              <span>뉴스</span>
            </div>
            <div className={`flex items-center ${
              watchlistItem.alerts.impactAlert ? 'text-electric-blue' : 'text-gray-400'
            }`}>
              <SparklesIcon className="h-4 w-4 mr-1" />
              <span>영향도</span>
            </div>
          </div>

          {/* 최근 뉴스 토글 */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
          >
            <span>최근 뉴스 {watchlistItem.recentNews.length}건</span>
            {isExpanded ? (
              <ChevronUpIcon className="h-4 w-4" />
            ) : (
              <ChevronDownIcon className="h-4 w-4" />
            )}
          </button>

          {/* 최근 뉴스 리스트 */}
          {isExpanded && (
            <div className="mt-3 space-y-2">
              {watchlistItem.recentNews.map((news, index) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-gray-900 dark:text-white flex-1">
                      {news.title}
                    </p>
                    <span className={`text-xs ml-2 ${
                      news.sentiment === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {news.sentiment === 'positive' ? '긍정' : '부정'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {news.date}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* 액션 버튼 */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => onViewDetails(watchlistItem)}
              className="flex-1 px-3 py-2 bg-electric-blue text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
            >
              상세 분석
            </button>
            <button
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium"
            >
              차트 보기
            </button>
          </div>
        </div>

        {/* 추가 날짜 */}
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {watchlistItem.addedAt}에 추가됨
          </p>
        </div>
      </div>

      {/* 알림 설정 모달 */}
      <AlertSettingsModal
        isOpen={showAlertSettings}
        onClose={() => setShowAlertSettings(false)}
        company={watchlistItem}
        alerts={watchlistItem.alerts}
        onSave={(alerts) => {
          onUpdateAlerts(watchlistItem.id, alerts)
          setShowAlertSettings(false)
        }}
      />
    </>
  )
}