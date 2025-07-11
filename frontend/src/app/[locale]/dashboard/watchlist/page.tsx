'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import DashboardLayout from '@/components/layout/DashboardLayout'
import WatchlistCard from '@/components/watchlist/WatchlistCard'
import AddCompanyModal from '@/components/watchlist/AddCompanyModal'
import WatchlistSummary from '@/components/watchlist/WatchlistSummary'
import { 
  BookmarkIcon,
  PlusIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

// 임시 관심 목록 데이터
const mockWatchlist = [
  {
    id: '1',
    companyId: '1',
    companyName: '삼성전자',
    category: '반도체',
    addedAt: '2024-01-15',
    currentPrice: '72,300원',
    priceChange: '+2.3%',
    priceChangeType: 'up' as const,
    marketCap: '400조원',
    impactScore: 0.92,
    recentNewsCount: 12,
    alerts: {
      priceAlert: true,
      newsAlert: true,
      impactAlert: true,
      thresholds: {
        priceChange: 5,
        impactScore: 0.8
      }
    },
    recentNews: [
      { title: "삼성전자, 3나노 양산 시작", date: "2시간 전", sentiment: "positive" },
      { title: "미국 반도체 보조금 65억 달러 확정", date: "5시간 전", sentiment: "positive" }
    ]
  },
  {
    id: '2',
    companyId: '4',
    companyName: 'LG에너지솔루션',
    category: '배터리',
    addedAt: '2024-01-10',
    currentPrice: '450,000원',
    priceChange: '-1.2%',
    priceChangeType: 'down' as const,
    marketCap: '100조원',
    impactScore: 0.88,
    recentNewsCount: 8,
    alerts: {
      priceAlert: true,
      newsAlert: false,
      impactAlert: true,
      thresholds: {
        priceChange: 3,
        impactScore: 0.85
      }
    },
    recentNews: [
      { title: "GM과 배터리 합작공장 확대", date: "3시간 전", sentiment: "positive" },
      { title: "원자재 가격 상승 우려", date: "1일 전", sentiment: "negative" }
    ]
  },
  {
    id: '3',
    companyId: '3',
    companyName: '현대자동차',
    category: '자동차',
    addedAt: '2024-01-08',
    currentPrice: '185,000원',
    priceChange: '+0.8%',
    priceChangeType: 'up' as const,
    marketCap: '50조원',
    impactScore: 0.78,
    recentNewsCount: 6,
    alerts: {
      priceAlert: false,
      newsAlert: true,
      impactAlert: false,
      thresholds: {
        priceChange: 5,
        impactScore: 0.7
      }
    },
    recentNews: [
      { title: "현대차, 인도 전기차 시장 진출", date: "4시간 전", sentiment: "positive" },
      { title: "UAW 파업 리스크 해소", date: "2일 전", sentiment: "positive" }
    ]
  }
]

// 추천 기업 데이터
const recommendedCompanies = [
  { id: '5', name: '현대로보틱스', category: '로보틱스', reason: '현대자동차 관련 기업' },
  { id: '2', name: 'SK하이닉스', category: '반도체', reason: '삼성전자와 유사 섹터' },
  { id: '6', name: '네이버', category: 'AI/플랫폼', reason: '높은 뉴스 영향도' }
]

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState(mockWatchlist)
  const [showAddModal, setShowAddModal] = useState(false)
  const [filter, setFilter] = useState<'all' | 'alerts' | 'positive' | 'negative'>('all')

  // 무료 사용자 제한 체크
  const isFreeTier = true // TODO: 실제 구독 상태 확인
  const watchlistLimit = isFreeTier ? 3 : 50
  const canAddMore = watchlist.length < watchlistLimit

  const handleAddCompany = (companyId: string) => {
    // 실제로는 API 호출
    console.log('Adding company:', companyId)
    setShowAddModal(false)
  }

  const handleRemoveCompany = (watchlistId: string) => {
    setWatchlist(watchlist.filter(item => item.id !== watchlistId))
  }

  const handleUpdateAlerts = (watchlistId: string, alerts: {
    priceAlert: boolean
    newsAlert: boolean
    impactAlert: boolean
    thresholds: {
      priceChange: number
      impactScore: number
    }
  }) => {
    setWatchlist(watchlist.map(item => 
      item.id === watchlistId ? { ...item, alerts } : item
    ))
  }

  const filteredWatchlist = watchlist.filter(item => {
    switch (filter) {
      case 'alerts':
        return item.alerts.priceAlert || item.alerts.newsAlert || item.alerts.impactAlert
      case 'positive':
        return item.priceChangeType === 'up'
      case 'negative':
        return item.priceChangeType === 'down'
      default:
        return true
    }
  })

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6">
          {/* 헤더 */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
                <BookmarkIcon className="h-6 w-6 mr-2" />
                관심 목록
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                관심 기업의 실시간 동향을 추적하고 알림을 받으세요
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              disabled={!canAddMore}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                canAddMore
                  ? 'bg-electric-blue text-white hover:bg-blue-600'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              }`}
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              기업 추가
            </button>
          </div>

          {/* 구독 상태 알림 */}
          {isFreeTier && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                <div>
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    무료 플랜: {watchlist.length}/{watchlistLimit}개 기업 사용 중
                  </p>
                  <p className="text-xs text-yellow-600 dark:text-yellow-300 mt-1">
                    더 많은 기업을 추가하려면 프리미엄으로 업그레이드하세요.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 요약 통계 */}
          <WatchlistSummary watchlist={watchlist} />

          {/* 필터 탭 */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {[
                { id: 'all', name: '전체', count: watchlist.length },
                { id: 'alerts', name: '알림 설정', count: watchlist.filter(w => w.alerts.priceAlert || w.alerts.newsAlert || w.alerts.impactAlert).length },
                { id: 'positive', name: '상승', count: watchlist.filter(w => w.priceChangeType === 'up').length },
                { id: 'negative', name: '하락', count: watchlist.filter(w => w.priceChangeType === 'down').length }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setFilter(tab.id as 'all' | 'alerts' | 'positive' | 'negative')}
                  className={`
                    whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
                    ${filter === tab.id
                      ? 'border-electric-blue text-electric-blue'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                    }
                  `}
                >
                  {tab.name}
                  <span className={`ml-2 ${
                    filter === tab.id ? 'text-electric-blue' : 'text-gray-400'
                  }`}>
                    ({tab.count})
                  </span>
                </button>
              ))}
            </nav>
          </div>

          {/* 관심 목록 */}
          {filteredWatchlist.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
              <BookmarkIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                관심 기업이 없습니다
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                기업을 추가하여 실시간 동향을 추적하세요.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setShowAddModal(true)}
                  disabled={!canAddMore}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-electric-blue hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-electric-blue"
                >
                  <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
                  첫 기업 추가하기
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredWatchlist.map((item) => (
                <WatchlistCard
                  key={item.id}
                  watchlistItem={item}
                  onRemove={handleRemoveCompany}
                  onUpdateAlerts={handleUpdateAlerts}
                  onViewDetails={(company) => console.log('View details:', company)}
                />
              ))}
            </div>
          )}

          {/* 추천 기업 */}
          {recommendedCompanies.length > 0 && canAddMore && (
            <div className="mt-8">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                추천 기업
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recommendedCompanies.map((company) => (
                  <div
                    key={company.id}
                    className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {company.name}
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {company.category}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {company.reason}
                        </p>
                      </div>
                      <button
                        onClick={() => handleAddCompany(company.id)}
                        className="text-electric-blue hover:text-blue-600"
                      >
                        <PlusIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 기업 추가 모달 */}
          <AddCompanyModal
            isOpen={showAddModal}
            onClose={() => setShowAddModal(false)}
            onAdd={handleAddCompany}
            currentWatchlist={watchlist.map(w => w.companyId)}
          />
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}