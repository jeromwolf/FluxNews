'use client'

import { Fragment } from 'react'
import { Transition } from '@headlessui/react'
import { Node } from 'reactflow'
import { 
  XMarkIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  NewspaperIcon,
  LinkIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'

interface CompanyDetailPanelProps {
  company: Node
  onClose: () => void
}

// 임시 상세 데이터
const mockCompanyDetails = {
  description: "대한민국 최대 전자 기업으로 반도체, 스마트폰, 가전제품을 생산합니다.",
  ceo: "한종희",
  founded: "1969년",
  employees: "267,937명",
  headquarters: "경기도 수원시",
  stockPrice: "72,300원",
  stockChange: "+2.3%",
  stockTrend: "up",
  relationships: [
    { company: "SK하이닉스", type: "기술 협력", strength: 0.8 },
    { company: "현대자동차", type: "부품 공급", strength: 0.6 },
    { company: "TSMC", type: "경쟁사", strength: 0.9 }
  ],
  recentNews: [
    { title: "삼성전자, 3나노 양산 시작", date: "2시간 전", sentiment: "positive" },
    { title: "미국 반도체 보조금 65억 달러 확정", date: "5시간 전", sentiment: "positive" },
    { title: "중국 시장 점유율 하락", date: "1일 전", sentiment: "negative" }
  ],
  keyMetrics: {
    revenue: "302.2조원",
    operatingProfit: "43.4조원",
    netIncome: "39.9조원",
    roe: "12.3%"
  }
}

export default function CompanyDetailPanel({ company, onClose }: CompanyDetailPanelProps) {
  const getSentimentColor = (sentiment: string) => {
    return sentiment === 'positive' ? 'text-green-600' : 'text-red-600'
  }

  return (
    <Transition
      show={true}
      as={Fragment}
      enter="transform transition ease-in-out duration-300"
      enterFrom="translate-x-full"
      enterTo="translate-x-0"
      leave="transform transition ease-in-out duration-300"
      leaveFrom="translate-x-0"
      leaveTo="translate-x-full"
    >
      <div className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-xl z-40 overflow-y-auto">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <BuildingOfficeIcon className="h-6 w-6 text-gray-600 dark:text-gray-400 mr-2" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {company.data.label}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* 기본 정보 */}
          <div className="mb-6">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {mockCompanyDetails.description}
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">CEO</span>
                <p className="font-medium text-gray-900 dark:text-white">{mockCompanyDetails.ceo}</p>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">설립</span>
                <p className="font-medium text-gray-900 dark:text-white">{mockCompanyDetails.founded}</p>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">직원 수</span>
                <p className="font-medium text-gray-900 dark:text-white">{mockCompanyDetails.employees}</p>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">본사</span>
                <p className="font-medium text-gray-900 dark:text-white">{mockCompanyDetails.headquarters}</p>
              </div>
            </div>
          </div>

          {/* 주가 정보 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center">
              <ChartBarIcon className="h-4 w-4 mr-2" />
              주가 정보
            </h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {mockCompanyDetails.stockPrice}
                </span>
                <div className={`flex items-center ${
                  mockCompanyDetails.stockTrend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {mockCompanyDetails.stockTrend === 'up' ? (
                    <ArrowTrendingUpIcon className="h-5 w-5 mr-1" />
                  ) : (
                    <ArrowTrendingDownIcon className="h-5 w-5 mr-1" />
                  )}
                  <span className="font-medium">{mockCompanyDetails.stockChange}</span>
                </div>
              </div>
            </div>
          </div>

          {/* 주요 지표 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
              주요 재무 지표
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                <span className="text-xs text-gray-500 dark:text-gray-400">매출액</span>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockCompanyDetails.keyMetrics.revenue}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                <span className="text-xs text-gray-500 dark:text-gray-400">영업이익</span>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockCompanyDetails.keyMetrics.operatingProfit}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                <span className="text-xs text-gray-500 dark:text-gray-400">순이익</span>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockCompanyDetails.keyMetrics.netIncome}
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                <span className="text-xs text-gray-500 dark:text-gray-400">ROE</span>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {mockCompanyDetails.keyMetrics.roe}
                </p>
              </div>
            </div>
          </div>

          {/* 관계 기업 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center">
              <LinkIcon className="h-4 w-4 mr-2" />
              관계 기업
            </h3>
            <div className="space-y-2">
              {mockCompanyDetails.relationships.map((rel, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{rel.company}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{rel.type}</p>
                  </div>
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                      <div 
                        className="bg-electric-blue h-2 rounded-full"
                        style={{ width: `${rel.strength * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {(rel.strength * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 최근 뉴스 */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center">
              <NewspaperIcon className="h-4 w-4 mr-2" />
              최근 뉴스
            </h3>
            <div className="space-y-2">
              {mockCompanyDetails.recentNews.map((news, index) => (
                <div key={index} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-gray-900 dark:text-white flex-1">
                      {news.title}
                    </p>
                    {news.sentiment === 'positive' ? (
                      <ChevronUpIcon className={`h-4 w-4 ml-2 ${getSentimentColor(news.sentiment)}`} />
                    ) : (
                      <ChevronDownIcon className={`h-4 w-4 ml-2 ${getSentimentColor(news.sentiment)}`} />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {news.date}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 영향도 점수 */}
          <div className="mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <SparklesIcon className="h-5 w-5 text-electric-blue mr-2" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    네트워크 영향도
                  </span>
                </div>
                <span className="text-2xl font-bold text-electric-blue">
                  {(company.data.impactScore * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                최근 30일간 {company.data.newsCount}건의 뉴스에서 언급
              </p>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="flex gap-3">
            <button className="flex-1 px-4 py-2 bg-electric-blue text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium">
              관심 목록에 추가
            </button>
            <button className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium">
              상세 분석
            </button>
          </div>
        </div>
      </div>
    </Transition>
  )
}