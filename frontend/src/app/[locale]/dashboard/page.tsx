'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import DashboardLayout from '@/components/layout/DashboardLayout'
import NewsCard from '@/components/news/NewsCard'
import SearchFilter from '@/components/news/SearchFilter'
import AIAnalysisModal from '@/components/news/AIAnalysisModal'
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline'

// 임시 뉴스 데이터
const mockNews = [
  {
    id: 1,
    title: "테슬라, 새로운 자율주행 칩 개발 발표",
    source: "Reuters",
    publishedAt: "2시간 전",
    summary: "테슬라가 차세대 자율주행 칩 개발을 발표했습니다. 이는 한국 반도체 기업들에게 새로운 기회가 될 수 있습니다.",
    impactScore: 0.85,
    sentiment: "positive" as const,
    companies: ["삼성전자", "SK하이닉스"],
    category: "자율주행",
    isHot: true
  },
  {
    id: 2,
    title: "현대자동차, 보스턴 다이내믹스와 로봇 기술 협력 확대",
    source: "Bloomberg",
    publishedAt: "4시간 전",
    summary: "현대자동차가 보스턴 다이내믹스와의 협력을 확대하여 산업용 로봇 개발에 박차를 가합니다.",
    impactScore: 0.72,
    sentiment: "positive" as const,
    companies: ["현대자동차", "현대로보틱스"],
    category: "로보틱스",
    isHot: false
  },
  {
    id: 3,
    title: "중국 BYD, 유럽 전기차 시장 공격적 진출",
    source: "Financial Times",
    publishedAt: "6시간 전",
    summary: "중국 BYD의 유럽 시장 진출로 한국 전기차 부품 업체들의 경쟁이 심화될 전망입니다.",
    impactScore: 0.68,
    sentiment: "negative" as const,
    companies: ["LG에너지솔루션", "삼성SDI"],
    category: "전기차",
    isHot: true
  }
]

const stats = [
  { name: '오늘의 뉴스', value: '127', change: '+12%', trend: 'up' },
  { name: 'AI 분석 완료', value: '89', change: '+5%', trend: 'up' },
  { name: '평균 영향도', value: '0.74', change: '-2%', trend: 'down' },
  { name: '관심 기업 알림', value: '23', change: '+18%', trend: 'up' },
]

export default function DashboardPage() {
  const [news, setNews] = useState(mockNews)
  const [selectedNews, setSelectedNews] = useState<typeof mockNews[0] | null>(null)
  const [showAnalysis, setShowAnalysis] = useState(false)

  const allCompanies = Array.from(new Set(mockNews.flatMap(n => n.companies)))
  const allCategories = Array.from(new Set(mockNews.map(n => n.category)))

  const handleSearch = (query: string) => {
    if (!query) {
      setNews(mockNews)
      return
    }
    
    const filtered = mockNews.filter(item => 
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.summary.toLowerCase().includes(query.toLowerCase()) ||
      item.companies.some(c => c.toLowerCase().includes(query.toLowerCase()))
    )
    setNews(filtered)
  }

  const handleFilterChange = (filters: {
    companies: string[]
    categories: string[]
    sentiment: 'all' | 'positive' | 'negative' | 'neutral'
    impactScore: number
    dateRange: 'all' | 'today' | 'week' | 'month'
  }) => {
    let filtered = [...mockNews]
    
    if (filters.companies.length > 0) {
      filtered = filtered.filter(item => 
        item.companies.some(c => filters.companies.includes(c))
      )
    }
    
    if (filters.categories.length > 0) {
      filtered = filtered.filter(item => 
        filters.categories.includes(item.category)
      )
    }
    
    if (filters.sentiment !== 'all') {
      filtered = filtered.filter(item => item.sentiment === filters.sentiment)
    }
    
    if (filters.impactScore > 0) {
      filtered = filtered.filter(item => 
        item.impactScore * 100 >= filters.impactScore
      )
    }
    
    setNews(filtered)
  }

  const handleAnalyze = (newsId: number) => {
    const newsItem = mockNews.find(n => n.id === newsId)
    if (newsItem) {
      setSelectedNews(newsItem)
      setShowAnalysis(true)
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
            {news.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400">
                  검색 결과가 없습니다.
                </p>
              </div>
            ) : (
              news.map((item) => (
                <NewsCard
                  key={item.id}
                  news={item}
                  onAnalyze={handleAnalyze}
                  onBookmark={(id) => console.log('Bookmark:', id)}
                  onShare={(id) => console.log('Share:', id)}
                />
              ))
            )}
          </div>
          
          {/* AI 분석 모달 */}
          {selectedNews && (
            <AIAnalysisModal
              isOpen={showAnalysis}
              onClose={() => {
                setShowAnalysis(false)
                setSelectedNews(null)
              }}
              news={selectedNews}
            />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}