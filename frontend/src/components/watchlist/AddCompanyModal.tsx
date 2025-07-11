'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { 
  XMarkIcon,
  MagnifyingGlassIcon,
  BuildingOfficeIcon,
  PlusIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

interface AddCompanyModalProps {
  isOpen: boolean
  onClose: () => void
  onAdd: (companyId: string) => void
  currentWatchlist: string[]
}

// 임시 기업 목록
const availableCompanies = [
  { id: '1', name: '삼성전자', category: '반도체', marketCap: '400조원' },
  { id: '2', name: 'SK하이닉스', category: '반도체', marketCap: '80조원' },
  { id: '3', name: '현대자동차', category: '자동차', marketCap: '50조원' },
  { id: '4', name: 'LG에너지솔루션', category: '배터리', marketCap: '100조원' },
  { id: '5', name: '현대로보틱스', category: '로보틱스', marketCap: '5조원' },
  { id: '6', name: '네이버', category: 'AI/플랫폼', marketCap: '60조원' },
  { id: '7', name: 'LG전자', category: '가전/로봇', marketCap: '20조원' },
  { id: '8', name: '삼성SDI', category: '배터리', marketCap: '40조원' },
  { id: '9', name: '기아', category: '자동차', marketCap: '35조원' },
  { id: '10', name: '현대모비스', category: '자동차부품', marketCap: '25조원' },
]

export default function AddCompanyModal({
  isOpen,
  onClose,
  onAdd,
  currentWatchlist
}: AddCompanyModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const categories = ['all', '반도체', '자동차', '배터리', '로보틱스', 'AI/플랫폼', '가전/로봇', '자동차부품']

  const filteredCompanies = availableCompanies.filter(company => {
    const matchesSearch = company.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || company.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const isInWatchlist = (companyId: string) => currentWatchlist.includes(companyId)

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
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                <div className="bg-white dark:bg-gray-800 px-4 pb-4 pt-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <BuildingOfficeIcon className="h-6 w-6 text-electric-blue mr-2" />
                      <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900 dark:text-white">
                        기업 추가
                      </Dialog.Title>
                    </div>
                    <button
                      onClick={onClose}
                      className="rounded-md bg-white dark:bg-gray-800 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-electric-blue"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  {/* 검색 및 필터 */}
                  <div className="mb-4 space-y-3">
                    <div className="relative">
                      <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="기업명 검색..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-700 dark:text-white"
                      />
                    </div>

                    <div className="flex gap-2 flex-wrap">
                      {categories.map(cat => (
                        <button
                          key={cat}
                          onClick={() => setSelectedCategory(cat)}
                          className={`px-3 py-1 text-sm rounded-full transition-colors ${
                            selectedCategory === cat
                              ? 'bg-electric-blue text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          }`}
                        >
                          {cat === 'all' ? '전체' : cat}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 기업 목록 */}
                  <div className="max-h-96 overflow-y-auto">
                    <div className="grid grid-cols-1 gap-2">
                      {filteredCompanies.map((company) => {
                        const isAdded = isInWatchlist(company.id)
                        
                        return (
                          <div
                            key={company.id}
                            className={`p-4 rounded-lg border transition-colors ${
                              isAdded
                                ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900'
                                : 'border-gray-200 dark:border-gray-700 hover:border-electric-blue hover:bg-blue-50 dark:hover:bg-blue-900/20'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900 dark:text-white">
                                  {company.name}
                                </h4>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {company.category} · {company.marketCap}
                                </p>
                              </div>
                              {isAdded ? (
                                <div className="flex items-center text-gray-500">
                                  <CheckIcon className="h-5 w-5 mr-1" />
                                  <span className="text-sm">추가됨</span>
                                </div>
                              ) : (
                                <button
                                  onClick={() => {
                                    onAdd(company.id)
                                    onClose()
                                  }}
                                  className="flex items-center px-3 py-1.5 bg-electric-blue text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                                >
                                  <PlusIcon className="h-4 w-4 mr-1" />
                                  추가
                                </button>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {filteredCompanies.length === 0 && (
                      <div className="text-center py-8">
                        <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                          검색 결과가 없습니다
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 px-4 py-3 sm:px-6">
                  <button
                    type="button"
                    onClick={onClose}
                    className="w-full inline-flex justify-center rounded-md bg-white dark:bg-gray-800 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    닫기
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