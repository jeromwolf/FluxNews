'use client'

import { useState, Fragment } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  CheckIcon,
  ChevronUpDownIcon
} from '@heroicons/react/24/outline'

interface SearchFilterProps {
  onSearch: (query: string) => void
  onFilterChange: (filters: FilterOptions) => void
  companies: string[]
  categories: string[]
}

interface FilterOptions {
  companies: string[]
  categories: string[]
  sentiment: 'all' | 'positive' | 'negative' | 'neutral'
  impactScore: number
  dateRange: 'all' | 'today' | 'week' | 'month'
}

const sentimentOptions = [
  { value: 'all', label: '전체' },
  { value: 'positive', label: '긍정적' },
  { value: 'negative', label: '부정적' },
  { value: 'neutral', label: '중립적' }
]

const dateRangeOptions = [
  { value: 'all', label: '전체 기간' },
  { value: 'today', label: '오늘' },
  { value: 'week', label: '이번 주' },
  { value: 'month', label: '이번 달' }
]

export default function SearchFilter({ onSearch, onFilterChange, companies, categories }: SearchFilterProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<FilterOptions>({
    companies: [],
    categories: [],
    sentiment: 'all',
    impactScore: 0,
    dateRange: 'all'
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(searchQuery)
  }

  const handleFilterChange = (key: keyof FilterOptions, value: FilterOptions[keyof FilterOptions]) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const resetFilters = () => {
    const defaultFilters: FilterOptions = {
      companies: [],
      categories: [],
      sentiment: 'all',
      impactScore: 0,
      dateRange: 'all'
    }
    setFilters(defaultFilters)
    onFilterChange(defaultFilters)
  }

  const activeFiltersCount = 
    filters.companies.length + 
    filters.categories.length + 
    (filters.sentiment !== 'all' ? 1 : 0) + 
    (filters.impactScore > 0 ? 1 : 0) + 
    (filters.dateRange !== 'all' ? 1 : 0)

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <form onSubmit={handleSearch} className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="뉴스 검색..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-800 dark:text-white"
            />
          </div>
        </form>
        
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center px-4 py-2 border rounded-lg transition-colors ${
            showFilters 
              ? 'border-electric-blue bg-electric-blue text-white' 
              : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <FunnelIcon className="h-5 w-5 mr-2" />
          필터
          {activeFiltersCount > 0 && (
            <span className="ml-2 bg-white text-electric-blue rounded-full px-2 py-0.5 text-xs font-medium">
              {activeFiltersCount}
            </span>
          )}
        </button>
      </div>

      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">상세 필터</h3>
            <button
              onClick={resetFilters}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              필터 초기화
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 기업 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                기업
              </label>
              <Listbox 
                value={filters.companies} 
                onChange={(value) => handleFilterChange('companies', value)}
                multiple
              >
                <div className="relative">
                  <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white dark:bg-gray-700 py-2 pl-3 pr-10 text-left shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 focus:outline-none focus:ring-2 focus:ring-electric-blue sm:text-sm">
                    <span className="block truncate">
                      {filters.companies.length === 0 
                        ? '전체 기업' 
                        : `${filters.companies.length}개 선택됨`}
                    </span>
                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </span>
                  </Listbox.Button>
                  <Transition
                    as={Fragment}
                    leave="transition ease-in duration-100"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-700 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                      {companies.map((company) => (
                        <Listbox.Option
                          key={company}
                          className={({ active }) =>
                            `relative cursor-default select-none py-2 pl-10 pr-4 ${
                              active ? 'bg-electric-blue text-white' : 'text-gray-900 dark:text-gray-300'
                            }`
                          }
                          value={company}
                        >
                          {({ selected, active }) => (
                            <>
                              <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                                {company}
                              </span>
                              {selected ? (
                                <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${
                                  active ? 'text-white' : 'text-electric-blue'
                                }`}>
                                  <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                </span>
                              ) : null}
                            </>
                          )}
                        </Listbox.Option>
                      ))}
                    </Listbox.Options>
                  </Transition>
                </div>
              </Listbox>
            </div>

            {/* 카테고리 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                카테고리
              </label>
              <Listbox 
                value={filters.categories} 
                onChange={(value) => handleFilterChange('categories', value)}
                multiple
              >
                <div className="relative">
                  <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white dark:bg-gray-700 py-2 pl-3 pr-10 text-left shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 focus:outline-none focus:ring-2 focus:ring-electric-blue sm:text-sm">
                    <span className="block truncate">
                      {filters.categories.length === 0 
                        ? '전체 카테고리' 
                        : `${filters.categories.length}개 선택됨`}
                    </span>
                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </span>
                  </Listbox.Button>
                  <Transition
                    as={Fragment}
                    leave="transition ease-in duration-100"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-700 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                      {categories.map((category) => (
                        <Listbox.Option
                          key={category}
                          className={({ active }) =>
                            `relative cursor-default select-none py-2 pl-10 pr-4 ${
                              active ? 'bg-electric-blue text-white' : 'text-gray-900 dark:text-gray-300'
                            }`
                          }
                          value={category}
                        >
                          {({ selected, active }) => (
                            <>
                              <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                                {category}
                              </span>
                              {selected ? (
                                <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${
                                  active ? 'text-white' : 'text-electric-blue'
                                }`}>
                                  <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                </span>
                              ) : null}
                            </>
                          )}
                        </Listbox.Option>
                      ))}
                    </Listbox.Options>
                  </Transition>
                </div>
              </Listbox>
            </div>

            {/* 감정 분석 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                감정 분석
              </label>
              <Listbox 
                value={filters.sentiment} 
                onChange={(value) => handleFilterChange('sentiment', value)}
              >
                <div className="relative">
                  <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white dark:bg-gray-700 py-2 pl-3 pr-10 text-left shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 focus:outline-none focus:ring-2 focus:ring-electric-blue sm:text-sm">
                    <span className="block truncate">
                      {sentimentOptions.find(opt => opt.value === filters.sentiment)?.label}
                    </span>
                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </span>
                  </Listbox.Button>
                  <Transition
                    as={Fragment}
                    leave="transition ease-in duration-100"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-700 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                      {sentimentOptions.map((option) => (
                        <Listbox.Option
                          key={option.value}
                          className={({ active }) =>
                            `relative cursor-default select-none py-2 pl-10 pr-4 ${
                              active ? 'bg-electric-blue text-white' : 'text-gray-900 dark:text-gray-300'
                            }`
                          }
                          value={option.value}
                        >
                          {({ selected, active }) => (
                            <>
                              <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                                {option.label}
                              </span>
                              {selected ? (
                                <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${
                                  active ? 'text-white' : 'text-electric-blue'
                                }`}>
                                  <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                </span>
                              ) : null}
                            </>
                          )}
                        </Listbox.Option>
                      ))}
                    </Listbox.Options>
                  </Transition>
                </div>
              </Listbox>
            </div>

            {/* 영향도 점수 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                최소 영향도: {filters.impactScore}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.impactScore}
                onChange={(e) => handleFilterChange('impactScore', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
            </div>

            {/* 날짜 범위 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                날짜 범위
              </label>
              <Listbox 
                value={filters.dateRange} 
                onChange={(value) => handleFilterChange('dateRange', value)}
              >
                <div className="relative">
                  <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white dark:bg-gray-700 py-2 pl-3 pr-10 text-left shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 focus:outline-none focus:ring-2 focus:ring-electric-blue sm:text-sm">
                    <span className="block truncate">
                      {dateRangeOptions.find(opt => opt.value === filters.dateRange)?.label}
                    </span>
                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </span>
                  </Listbox.Button>
                  <Transition
                    as={Fragment}
                    leave="transition ease-in duration-100"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-gray-700 py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                      {dateRangeOptions.map((option) => (
                        <Listbox.Option
                          key={option.value}
                          className={({ active }) =>
                            `relative cursor-default select-none py-2 pl-10 pr-4 ${
                              active ? 'bg-electric-blue text-white' : 'text-gray-900 dark:text-gray-300'
                            }`
                          }
                          value={option.value}
                        >
                          {({ selected, active }) => (
                            <>
                              <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                                {option.label}
                              </span>
                              {selected ? (
                                <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${
                                  active ? 'text-white' : 'text-electric-blue'
                                }`}>
                                  <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                </span>
                              ) : null}
                            </>
                          )}
                        </Listbox.Option>
                      ))}
                    </Listbox.Options>
                  </Transition>
                </div>
              </Listbox>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}