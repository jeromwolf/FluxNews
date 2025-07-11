'use client'

import { 
  ClockIcon,
  FireIcon,
  SparklesIcon,
  BookmarkIcon,
  ShareIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid'
import { useState } from 'react'

interface NewsCardProps {
  news: {
    id: number
    title: string
    source: string
    publishedAt: string
    summary: string
    impactScore: number
    sentiment: 'positive' | 'negative' | 'neutral'
    companies: string[]
    category: string
    isHot: boolean
  }
  onBookmark?: (id: number) => void
  onShare?: (id: number) => void
  onAnalyze?: (id: number) => void
}

export default function NewsCard({ news, onBookmark, onShare, onAnalyze }: NewsCardProps) {
  const [isBookmarked, setIsBookmarked] = useState(false)

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked)
    onBookmark?.(news.id)
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'negative':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
    }
  }

  const getSentimentText = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return '긍정적'
      case 'negative':
        return '부정적'
      default:
        return '중립적'
    }
  }

  const getImpactColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600 dark:text-red-400'
    if (score >= 0.6) return 'text-orange-600 dark:text-orange-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center">
            {news.isHot && (
              <FireIcon className="h-5 w-5 text-red-500 mr-2 flex-shrink-0" />
            )}
            <h3 className="text-lg font-medium text-gray-900 dark:text-white line-clamp-2">
              {news.title}
            </h3>
          </div>
          
          <div className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
            <span>{news.source}</span>
            <span className="mx-2">•</span>
            <ClockIcon className="h-4 w-4 mr-1" />
            <span>{news.publishedAt}</span>
            <span className="mx-2">•</span>
            <span className="text-electric-blue">{news.category}</span>
          </div>
          
          <p className="mt-2 text-gray-600 dark:text-gray-300 line-clamp-3">
            {news.summary}
          </p>
          
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <SparklesIcon className={`h-5 w-5 mr-1 ${getImpactColor(news.impactScore)}`} />
                <span className={`text-sm font-medium ${getImpactColor(news.impactScore)}`}>
                  영향도: {(news.impactScore * 100).toFixed(0)}%
                </span>
              </div>
              <div className={`flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(news.sentiment)}`}>
                {getSentimentText(news.sentiment)}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {news.companies.map((company) => (
                <span
                  key={company}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                >
                  {company}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 flex items-center space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleBookmark}
              className="flex items-center space-x-1 text-gray-500 hover:text-electric-blue transition-colors"
              title="북마크"
            >
              {isBookmarked ? (
                <BookmarkSolidIcon className="h-5 w-5 text-electric-blue" />
              ) : (
                <BookmarkIcon className="h-5 w-5" />
              )}
              <span className="text-sm">저장</span>
            </button>
            
            <button
              onClick={() => onShare?.(news.id)}
              className="flex items-center space-x-1 text-gray-500 hover:text-electric-blue transition-colors"
              title="공유"
            >
              <ShareIcon className="h-5 w-5" />
              <span className="text-sm">공유</span>
            </button>
            
            <button
              onClick={() => onAnalyze?.(news.id)}
              className="flex items-center space-x-1 text-gray-500 hover:text-electric-blue transition-colors"
              title="상세 분석"
            >
              <ChartBarIcon className="h-5 w-5" />
              <span className="text-sm">상세 분석</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}