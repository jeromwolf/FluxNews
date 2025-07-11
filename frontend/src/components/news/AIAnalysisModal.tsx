'use client'

import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { 
  XMarkIcon,
  SparklesIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface AIAnalysisModalProps {
  isOpen: boolean
  onClose: () => void
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
  }
  analysis?: {
    detailedSummary: string
    keyPoints: string[]
    affectedCompanies: {
      name: string
      impact: 'high' | 'medium' | 'low'
      reason: string
    }[]
    marketImpact: {
      sector: string
      trend: 'up' | 'down' | 'neutral'
      percentage: number
    }[]
    recommendations: string[]
    confidence: number
  }
}

export default function AIAnalysisModal({ isOpen, onClose, news, analysis }: AIAnalysisModalProps) {
  // 임시 분석 데이터
  const mockAnalysis = analysis || {
    detailedSummary: "테슬라의 새로운 자율주행 칩 개발은 한국 반도체 산업에 중요한 기회를 제공합니다. 특히 삼성전자와 SK하이닉스는 차세대 AI 칩 생산에서 핵심 파트너가 될 가능성이 높습니다.",
    keyPoints: [
      "5nm 공정 기술을 활용한 고성능 AI 칩 수요 증가",
      "한국 반도체 기업의 파운드리 서비스 수주 가능성",
      "자율주행 시장 확대에 따른 장기적 성장 기회"
    ],
    affectedCompanies: [
      { name: "삼성전자", impact: "high", reason: "파운드리 사업부 직접 수혜 예상" },
      { name: "SK하이닉스", impact: "medium", reason: "HBM 메모리 공급 기회" },
      { name: "현대자동차", impact: "low", reason: "경쟁사 기술 발전으로 간접 영향" }
    ],
    marketImpact: [
      { sector: "반도체", trend: "up", percentage: 3.5 },
      { sector: "자동차", trend: "neutral", percentage: 0.2 }
    ],
    recommendations: [
      "삼성전자 및 SK하이닉스 주식 매수 고려",
      "반도체 섹터 ETF 편입 비중 확대",
      "테슬라 공급망 관련 기업 모니터링 강화"
    ],
    confidence: 0.82
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/20'
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/20'
      case 'low': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20'
      default: return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/20'
    }
  }

  const getImpactText = (impact: string) => {
    switch (impact) {
      case 'high': return '높음'
      case 'medium': return '중간'
      case 'low': return '낮음'
      default: return '미정'
    }
  }

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
                <div className="bg-white dark:bg-gray-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <SparklesIcon className="h-6 w-6 text-electric-blue mr-2" />
                      <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900 dark:text-white">
                        AI 상세 분석
                      </Dialog.Title>
                    </div>
                    <button
                      onClick={onClose}
                      className="rounded-md bg-white dark:bg-gray-800 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-electric-blue"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  <div className="space-y-6">
                    {/* 뉴스 정보 */}
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                      <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                        {news.title}
                      </h4>
                      <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                        <span>{news.source}</span>
                        <span className="mx-2">•</span>
                        <span>{news.publishedAt}</span>
                        <span className="mx-2">•</span>
                        <span className="text-electric-blue">{news.category}</span>
                      </div>
                    </div>

                    {/* AI 신뢰도 */}
                    <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                      <div className="flex items-center">
                        <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                        <span className="text-sm font-medium text-blue-900 dark:text-blue-300">
                          AI 분석 신뢰도
                        </span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                          <div 
                            className="bg-electric-blue h-2 rounded-full"
                            style={{ width: `${mockAnalysis.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {(mockAnalysis.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* 상세 요약 */}
                    <div>
                      <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                        상세 분석
                      </h4>
                      <p className="text-gray-600 dark:text-gray-300">
                        {mockAnalysis.detailedSummary}
                      </p>
                    </div>

                    {/* 핵심 포인트 */}
                    <div>
                      <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                        핵심 포인트
                      </h4>
                      <ul className="space-y-2">
                        {mockAnalysis.keyPoints.map((point, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-electric-blue mr-2">•</span>
                            <span className="text-gray-600 dark:text-gray-300">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* 영향 받는 기업 */}
                    <div>
                      <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                        <BuildingOfficeIcon className="h-5 w-5 mr-2" />
                        영향 받는 기업
                      </h4>
                      <div className="space-y-2">
                        {mockAnalysis.affectedCompanies.map((company) => (
                          <div key={company.name} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center">
                                <span className="font-medium text-gray-900 dark:text-white">
                                  {company.name}
                                </span>
                                <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${getImpactColor(company.impact)}`}>
                                  영향도: {getImpactText(company.impact)}
                                </span>
                              </div>
                              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                {company.reason}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 시장 영향 */}
                    <div>
                      <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                        <ChartBarIcon className="h-5 w-5 mr-2" />
                        시장 영향
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        {mockAnalysis.marketImpact.map((impact) => (
                          <div key={impact.sector} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {impact.sector}
                              </span>
                              <div className="flex items-center">
                                {impact.trend === 'up' ? (
                                  <ArrowTrendingUpIcon className="h-5 w-5 text-green-600 mr-1" />
                                ) : impact.trend === 'down' ? (
                                  <ArrowTrendingDownIcon className="h-5 w-5 text-red-600 mr-1" />
                                ) : null}
                                <span className={`text-sm font-medium ${
                                  impact.trend === 'up' ? 'text-green-600' : 
                                  impact.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                                }`}>
                                  {impact.trend === 'up' ? '+' : ''}{impact.percentage}%
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 투자 추천 사항 */}
                    <div>
                      <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                        투자 추천 사항
                      </h4>
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <ul className="space-y-2">
                          {mockAnalysis.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-yellow-600 dark:text-yellow-400 mr-2">▶</span>
                              <span className="text-gray-700 dark:text-gray-300">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    className="inline-flex w-full justify-center rounded-md bg-electric-blue px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 sm:ml-3 sm:w-auto"
                    onClick={onClose}
                  >
                    확인
                  </button>
                  <button
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-gray-800 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 sm:mt-0 sm:w-auto"
                    onClick={onClose}
                  >
                    PDF로 저장
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}