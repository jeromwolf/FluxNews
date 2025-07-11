'use client'

import { useState } from 'react'
import { 
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowsRightLeftIcon
} from '@heroicons/react/24/outline'

interface NetworkFiltersProps {
  onFilterChange: (filters: NetworkFilterOptions) => void
  onLayoutChange: (layout: string) => void
  onToggleLabels: () => void
  showLabels: boolean
}

interface NetworkFilterOptions {
  minImpactScore: number
  minNewsCount: number
  relationshipTypes: string[]
  showOnlyConnected: boolean
}

const relationshipTypes = [
  { value: 'all', label: '모든 관계' },
  { value: 'subsidiary', label: '자회사' },
  { value: 'partner', label: '파트너' },
  { value: 'supplier', label: '공급업체' },
  { value: 'competitor', label: '경쟁사' },
  { value: 'investor', label: '투자자' }
]

const layoutOptions = [
  { value: 'force', label: '자동 배치' },
  { value: 'hierarchical', label: '계층형' },
  { value: 'circular', label: '원형' },
  { value: 'grid', label: '격자형' }
]

export default function NetworkFilters({ 
  onFilterChange, 
  onLayoutChange, 
  onToggleLabels, 
  showLabels 
}: NetworkFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [filters, setFilters] = useState<NetworkFilterOptions>({
    minImpactScore: 0,
    minNewsCount: 0,
    relationshipTypes: ['all'],
    showOnlyConnected: false
  })
  const [selectedLayout, setSelectedLayout] = useState('force')

  const handleFilterChange = (key: keyof NetworkFilterOptions, value: NetworkFilterOptions[keyof NetworkFilterOptions]) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleLayoutChange = (layout: string) => {
    setSelectedLayout(layout)
    onLayoutChange(layout)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center">
          <FunnelIcon className="h-4 w-4 mr-2" />
          네트워크 필터
        </h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-electric-blue hover:text-blue-600 flex items-center"
        >
          <AdjustmentsHorizontalIcon className="h-4 w-4 mr-1" />
          {showAdvanced ? '간단히' : '고급 옵션'}
        </button>
      </div>

      {/* 기본 필터 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 영향도 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            최소 영향도: {filters.minImpactScore}%
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.minImpactScore}
            onChange={(e) => handleFilterChange('minImpactScore', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        {/* 뉴스 수 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            최소 뉴스 수: {filters.minNewsCount}건
          </label>
          <input
            type="range"
            min="0"
            max="50"
            value={filters.minNewsCount}
            onChange={(e) => handleFilterChange('minNewsCount', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        {/* 레이아웃 선택 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            레이아웃
          </label>
          <select
            value={selectedLayout}
            onChange={(e) => handleLayoutChange(e.target.value)}
            className="w-full px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-700 dark:text-white text-sm"
          >
            {layoutOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 고급 옵션 */}
      {showAdvanced && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 관계 유형 필터 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                관계 유형
              </label>
              <div className="space-y-2">
                {relationshipTypes.map(type => (
                  <label key={type.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.relationshipTypes.includes(type.value)}
                      onChange={(e) => {
                        const newTypes = e.target.checked
                          ? [...filters.relationshipTypes, type.value]
                          : filters.relationshipTypes.filter(t => t !== type.value)
                        handleFilterChange('relationshipTypes', newTypes)
                      }}
                      className="h-4 w-4 text-electric-blue focus:ring-electric-blue border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      {type.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* 추가 옵션 */}
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showOnlyConnected}
                  onChange={(e) => handleFilterChange('showOnlyConnected', e.target.checked)}
                  className="h-4 w-4 text-electric-blue focus:ring-electric-blue border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  연결된 기업만 표시
                </span>
              </label>

              <button
                onClick={onToggleLabels}
                className={`flex items-center px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  showLabels
                    ? 'bg-electric-blue text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                {showLabels ? (
                  <>
                    <EyeIcon className="h-4 w-4 mr-2" />
                    라벨 표시 중
                  </>
                ) : (
                  <>
                    <EyeSlashIcon className="h-4 w-4 mr-2" />
                    라벨 숨김
                  </>
                )}
              </button>

              <button className="flex items-center px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm">
                <ArrowsRightLeftIcon className="h-4 w-4 mr-2" />
                관계 강도 표시
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 필터 요약 */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            영향도 {filters.minImpactScore}% 이상, 뉴스 {filters.minNewsCount}건 이상
            {filters.showOnlyConnected && ', 연결된 기업만'}
          </p>
          <button
            onClick={() => {
              const defaultFilters: NetworkFilterOptions = {
                minImpactScore: 0,
                minNewsCount: 0,
                relationshipTypes: ['all'],
                showOnlyConnected: false
              }
              setFilters(defaultFilters)
              onFilterChange(defaultFilters)
            }}
            className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            필터 초기화
          </button>
        </div>
      </div>
    </div>
  )
}