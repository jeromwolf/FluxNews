'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import DashboardLayout from '@/components/layout/DashboardLayout'
import WatchlistCard from '@/components/watchlist/WatchlistCard'
import AddCompanyModal from '@/components/watchlist/AddCompanyModal'
import WatchlistSummary from '@/components/watchlist/WatchlistSummary'
import AlertSettingsModal from '@/components/watchlist/AlertSettingsModal'
import { useWatchlist, useWatchlistAlerts } from '@/hooks/useWatchlist'
import { useCompanySearch } from '@/hooks/useCompanies'
import { 
  BookmarkIcon,
  PlusIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

// 추천 기업 데이터 (임시)
const recommendedCompanies = [
  { id: 5, name: '현대로보틱스', category: '로보틱스', reason: '현대자동차 관련 기업' },
  { id: 2, name: 'SK하이닉스', category: '반도체', reason: '삼성전자와 유사 섹터' },
  { id: 6, name: '네이버', category: 'AI/플랫폼', reason: 'AI 기술 투자' }
]

export default function WatchlistPage() {
  const { watchlist, loading, error, addToWatchlist, removeFromWatchlist, updateWatchlistItem } = useWatchlist()
  const { alerts } = useWatchlistAlerts()
  const { searchCompanies } = useCompanySearch()
  
  const [showAddModal, setShowAddModal] = useState(false)
  const [showAlertSettings, setShowAlertSettings] = useState(false)
  const [selectedWatchlistItem, setSelectedWatchlistItem] = useState<any>(null)

  const handleRemove = async (watchlistId: number) => {
    try {
      await removeFromWatchlist(watchlistId)
    } catch (error) {
      console.error('Failed to remove from watchlist:', error)
    }
  }

  const handleAlertSettings = (item: any) => {
    setSelectedWatchlistItem(item)
    setShowAlertSettings(true)
  }

  const handleUpdateAlerts = async (alertEnabled: boolean, alertThreshold?: number) => {
    if (!selectedWatchlistItem) return
    
    try {
      await updateWatchlistItem(selectedWatchlistItem.id, alertEnabled, alertThreshold)
      setShowAlertSettings(false)
      setSelectedWatchlistItem(null)
    } catch (error) {
      console.error('Failed to update alerts:', error)
    }
  }

  const handleAddCompany = async (companyId: number, alertEnabled: boolean, alertThreshold?: number) => {
    try {
      await addToWatchlist(companyId, alertEnabled, alertThreshold)
      setShowAddModal(false)
    } catch (error) {
      console.error('Failed to add to watchlist:', error)
    }
  }

  const summary = {
    totalCompanies: watchlist.length,
    upCount: 0, // 실시간 가격 데이터 필요
    downCount: 0, // 실시간 가격 데이터 필요
    alertCount: watchlist.filter(item => item.alert_enabled).length,
    avgImpactScore: watchlist.reduce((sum, item) => sum + (item.recent_impact_score || 0), 0) / watchlist.length || 0
  }

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
                관심 기업들의 뉴스와 영향도를 실시간으로 모니터링합니다
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-electric-blue hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-electric-blue transition-colors"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              기업 추가
            </button>
          </div>

          {/* 요약 통계 */}
          <WatchlistSummary summary={summary} />

          {/* 메인 컨텐츠 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 왼쪽: 관심 목록 */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                내 관심 기업 ({watchlist.length}/3)
              </h2>
              
              {/* 관심 목록 */}
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-electric-blue mx-auto"></div>
                  <p className="mt-4 text-gray-500 dark:text-gray-400">관심목록 불러오는 중...</p>
                </div>
              ) : error ? (
                <div className="text-center py-12">
                  <p className="text-red-500">오류: {error}</p>
                </div>
              ) : watchlist.length === 0 ? (
                <div className="text-center py-12">
                  <BookmarkIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    관심 기업이 없습니다
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    기업을 추가하여 실시간으로 모니터링하세요
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {watchlist.map((item) => (
                    <WatchlistCard
                      key={item.id}
                      company={{
                        id: item.id.toString(),
                        companyId: item.company_id.toString(),
                        companyName: item.company_name,
                        category: item.company_sector,
                        addedAt: new Date(item.created_at).toLocaleDateString(),
                        currentPrice: '0원', // 실시간 가격 데이터 필요
                        priceChange: '0%',
                        priceChangeType: 'neutral' as const,
                        marketCap: 'N/A',
                        impactScore: item.recent_impact_score || 0,
                        recentNewsCount: 0,
                        alerts: {
                          priceAlert: false,
                          newsAlert: false,
                          impactAlert: item.alert_enabled,
                          thresholds: {
                            priceChange: 0,
                            impactScore: item.alert_threshold || 0
                          }
                        },
                        recentNews: []
                      }}
                      onRemove={() => handleRemove(item.id)}
                      onAlertSettings={() => handleAlertSettings(item)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* 오른쪽: 추천 및 알림 */}
            <div className="space-y-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                추천 및 알림
              </h2>

              {/* 알림 */}
              {alerts.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <div className="flex items-start">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                        최근 트리거된 알림
                      </h3>
                      <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                        <ul className="list-disc list-inside space-y-1">
                          {alerts.slice(0, 5).map((alert, index) => (
                            <li key={index}>
                              <span className="font-medium">{alert.company_name}</span>: 
                              영향도 {(alert.impact_score * 100).toFixed(0)}% 
                              (임계치 {(alert.threshold * 100).toFixed(0)}% 초과)
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 추천 기업 */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  추천 기업
                </h3>
                <div className="space-y-3">
                  {recommendedCompanies.map((company) => (
                    <div key={company.id} className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {company.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {company.category} • {company.reason}
                        </p>
                      </div>
                      <button
                        onClick={() => handleAddCompany(company.id, false)}
                        className="ml-2 p-1 text-electric-blue hover:text-blue-600 transition-colors"
                      >
                        <PlusIcon className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 기업 추가 모달 */}
          <AddCompanyModal
            isOpen={showAddModal}
            onClose={() => setShowAddModal(false)}
            onAdd={handleAddCompany}
            recommendedCompanies={recommendedCompanies}
          />

          {/* 알림 설정 모달 */}
          {selectedWatchlistItem && (
            <AlertSettingsModal
              isOpen={showAlertSettings}
              onClose={() => {
                setShowAlertSettings(false)
                setSelectedWatchlistItem(null)
              }}
              companyName={selectedWatchlistItem.company_name}
              currentSettings={{
                enabled: selectedWatchlistItem.alert_enabled,
                threshold: selectedWatchlistItem.alert_threshold
              }}
              onSave={handleUpdateAlerts}
            />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}