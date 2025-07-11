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
import type { AIAnalysisResponse } from '@/types/api'

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
  analysis?: AIAnalysisResponse | null
  loading?: boolean
}

export default function AIAnalysisModal({ isOpen, onClose, news, analysis, loading }: AIAnalysisModalProps) {
  const getSentimentConfidence = () => {
    if (!analysis) return 0.7
    const sentiment = analysis.sentiment
    return Math.max(sentiment.positive, sentiment.negative, sentiment.neutral)
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
                            style={{ width: `${getSentimentConfidence() * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {(getSentimentConfidence() * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* 상세 요약 */}
                    {loading ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-electric-blue mx-auto"></div>
                        <p className="mt-4 text-gray-500 dark:text-gray-400">AI가 분석 중입니다...</p>
                      </div>
                    ) : analysis ? (
                      <div>
                        <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                          상세 분석
                        </h4>
                        <p className="text-gray-600 dark:text-gray-300">
                          {analysis.summary}
                        </p>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        분석 데이터를 불러오는 중입니다...
                      </div>
                    )}

                    {/* 핵심 기업 */}
                    {analysis && analysis.key_companies.length > 0 && (
                      <div>
                        <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2">
                          핵심 기업
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {analysis.key_companies.map((company, index) => (
                            <div key={index} className="bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2">
                              <div className="font-medium text-gray-900 dark:text-white">
                                {company.name}
                              </div>
                              {company.ticker && (
                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                  {company.ticker}
                                </div>
                              )}
                              {company.role && (
                                <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                                  {company.role}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 영향 분석 */}
                    {analysis && Object.keys(analysis.impact_analysis).length > 0 && (
                      <div>
                        <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                          <BuildingOfficeIcon className="h-5 w-5 mr-2" />
                          기업별 영향 분석
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(analysis.impact_analysis).map(([company, impact]) => (
                            <div key={company} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                              <div className="flex-1">
                                <div className="flex items-center">
                                  <span className="font-medium text-gray-900 dark:text-white">
                                    {company}
                                  </span>
                                  <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${
                                    impact.impact === 'positive' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20' :
                                    impact.impact === 'negative' ? 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/20' :
                                    'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/20'
                                  }`}>
                                    {impact.impact === 'positive' ? '긍정적' : impact.impact === 'negative' ? '부정적' : '중립'}
                                  </span>
                                  <span className="ml-2 text-sm font-medium text-gray-600 dark:text-gray-400">
                                    {(impact.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                  {impact.reason}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 감정 분석 */}
                    {analysis && (
                      <div>
                        <h4 className="text-base font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                          <ChartBarIcon className="h-5 w-5 mr-2" />
                          감정 분석
                        </h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                            <div className="text-sm font-medium text-green-900 dark:text-green-300">
                              긍정
                            </div>
                            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                              {(analysis.sentiment.positive * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div className="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-300">
                              중립
                            </div>
                            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                              {(analysis.sentiment.neutral * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                            <div className="text-sm font-medium text-red-900 dark:text-red-300">
                              부정
                            </div>
                            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                              {(analysis.sentiment.negative * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 투자 참고 사항 */}
                    {analysis && (
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <div className="flex items-center mb-2">
                          <InformationCircleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                          <h4 className="text-base font-medium text-yellow-900 dark:text-yellow-300">
                            투자 참고 사항
                          </h4>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          이 분석은 AI가 생성한 참고 자료이며, 투자 결정의 유일한 근거가 되어서는 안 됩니다. 
                          실제 투자 전 반드시 전문가와 상담하시기 바랍니다.
                        </p>
                      </div>
                    )}
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