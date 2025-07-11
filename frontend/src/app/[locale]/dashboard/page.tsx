'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import DashboardLayout from '@/components/layout/DashboardLayout'
import NewsCard from '@/components/news/NewsCard'
import SearchFilter from '@/components/news/SearchFilter'
import AIAnalysisModal from '@/components/news/AIAnalysisModal'
import { useNewsFeed, useAIAnalysis } from '@/hooks/useNews'
import { useAuth } from '@/hooks/useAuth'
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline'
import type { NewsArticle, AIAnalysisResponse } from '@/types/api'

// 시간 포맷 함수
const formatTimeAgo = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
  
  if (diffInHours < 1) {
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    return `${diffInMinutes}분 전`
  } else if (diffInHours < 24) {
    return `${diffInHours}시간 전`
  } else {
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}일 전`
  }
}

const stats = [
  { name: '오늘의 뉴스', value: '127', change: '+12%', trend: 'up' },
  { name: 'AI 분석 완료', value: '89', change: '+5%', trend: 'up' },
  { name: '평균 영향도', value: '0.74', change: '-2%', trend: 'down' },
  { name: '관심 기업 알림', value: '23', change: '+18%', trend: 'up' },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const { articles, loading, error, loadMore, hasMore, refresh } = useNewsFeed()
  const { analyzeArticle, analyzing } = useAIAnalysis()
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null)
  const [analysisData, setAnalysisData] = useState<AIAnalysisResponse | null>(null)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [filteredArticles, setFilteredArticles] = useState<NewsArticle[]>([])

  useEffect(() => {
    setFilteredArticles(articles)
  }, [articles])

  // 임시 카테고리 및 회사 목록 (실제로는 API에서 가져와야 함)
  const allCompanies = ['삼성전자', 'SK하이닉스', '현대자동차', 'LG에너지솔루션', '현대로보틱스']
  const allCategories = ['자율주행', '로보틱스', '전기차', 'AI', '반도체']

  const handleSearch = (query: string) => {
    if (!query) {
      setFilteredArticles(articles)
      return
    }
    
    const filtered = articles.filter(item => 
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.content.toLowerCase().includes(query.toLowerCase())
    )
    setFilteredArticles(filtered)
  }

  const handleFilterChange = (filters: {
    companies: string[]
    categories: string[]
    sentiment: 'all' | 'positive' | 'negative' | 'neutral'
    impactScore: number
    dateRange: 'all' | 'today' | 'week' | 'month'
  }) => {
    let filtered = [...articles]
    
    // 날짜 필터
    if (filters.dateRange !== 'all') {
      const now = new Date()
      const filterDate = new Date()
      
      switch (filters.dateRange) {
        case 'today':
          filterDate.setDate(now.getDate() - 1)
          break
        case 'week':
          filterDate.setDate(now.getDate() - 7)
          break
        case 'month':
          filterDate.setMonth(now.getMonth() - 1)
          break
      }
      
      filtered = filtered.filter(item => 
        new Date(item.published_date) >= filterDate
      )
    }
    
    // 감정 점수 필터
    if (filters.sentiment !== 'all' && filters.impactScore > 0) {
      filtered = filtered.filter(item => 
        item.sentiment_score && item.sentiment_score >= filters.impactScore / 100
      )
    }
    
    setFilteredArticles(filtered)
  }

  const handleAnalyze = async (articleId: number) => {
    const article = articles.find(a => a.id === articleId)
    if (article && user) {
      setSelectedArticle(article)
      setShowAnalysis(true)
      
      const analysis = await analyzeArticle(articleId, user.id)
      if (analysis) {
        setAnalysisData(analysis)
      }
    }
  }

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6">
          {/* 헤더 */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              뉴스 피드
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              글로벌 뉴스가 한국 기업에 미치는 영향을 실시간으로 분석합니다
            </p>
          </div>

          {/* 통계 카드 */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.name}
                className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg"
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {stat.trend === 'up' ? (
                        <ArrowTrendingUpIcon className="h-6 w-6 text-green-600" />
                      ) : (
                        <ArrowTrendingDownIcon className="h-6 w-6 text-red-600" />
                      )}
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          {stat.name}
                        </dt>
                        <dd className="flex items-baseline">
                          <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                            {stat.value}
                          </div>
                          <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                            stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {stat.change}
                          </div>
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 검색 및 필터 */}
          <SearchFilter
            onSearch={handleSearch}
            onFilterChange={handleFilterChange}
            companies={allCompanies}
            categories={allCategories}
          />

          {/* 뉴스 리스트 */}
          <div className="space-y-4">
            {loading && filteredArticles.length === 0 ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-electric-blue mx-auto"></div>
                <p className="mt-4 text-gray-500 dark:text-gray-400">뉴스를 불러오는 중...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-500">오류가 발생했습니다: {error}</p>
                <button
                  onClick={refresh}
                  className="mt-4 px-4 py-2 bg-electric-blue text-white rounded hover:bg-blue-600"
                >
                  다시 시도
                </button>
              </div>
            ) : filteredArticles.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400">
                  검색 결과가 없습니다.
                </p>
              </div>
            ) : (
              <>
                {filteredArticles.map((article) => (
                  <NewsCard
                    key={article.id}
                    news={{
                      id: article.id,
                      title: article.title,
                      source: article.source,
                      publishedAt: formatTimeAgo(article.published_date),
                      summary: article.content.substring(0, 200) + '...',
                      impactScore: article.sentiment_score || 0.5,
                      sentiment: article.sentiment_score ? 
                        (article.sentiment_score > 0.6 ? 'positive' : 
                         article.sentiment_score < 0.4 ? 'negative' : 'neutral') : 'neutral',
                      companies: [],
                      category: '뉴스',
                      isHot: article.processed
                    }}
                    onAnalyze={handleAnalyze}
                    onBookmark={(id) => console.log('Bookmark:', id)}
                    onShare={(id) => console.log('Share:', id)}
                  />
                ))}
                {hasMore && (
                  <div className="text-center py-4">
                    <button
                      onClick={loadMore}
                      disabled={loading}
                      className="px-6 py-2 bg-electric-blue text-white rounded hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? '로딩 중...' : '더 보기'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
          
          {/* AI 분석 모달 */}
          {selectedArticle && (
            <AIAnalysisModal
              isOpen={showAnalysis}
              onClose={() => {
                setShowAnalysis(false)
                setSelectedArticle(null)
                setAnalysisData(null)
              }}
              news={{
                id: selectedArticle.id,
                title: selectedArticle.title,
                source: selectedArticle.source,
                publishedAt: formatTimeAgo(selectedArticle.published_date),
                summary: selectedArticle.content.substring(0, 200) + '...',
                impactScore: selectedArticle.sentiment_score || 0.5,
                sentiment: selectedArticle.sentiment_score ? 
                  (selectedArticle.sentiment_score > 0.6 ? 'positive' : 
                   selectedArticle.sentiment_score < 0.4 ? 'negative' : 'neutral') : 'neutral',
                companies: analysisData?.key_companies.map(c => c.name) || [],
                category: '뉴스',
                isHot: selectedArticle.processed
              }}
              analysis={analysisData}
              loading={analyzing}
            />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}