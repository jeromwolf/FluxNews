'use client'

import { Fragment, useState } from 'react'
import { Dialog, Transition, Switch } from '@headlessui/react'
import { 
  XMarkIcon,
  BellIcon,
  ChartBarIcon,
  NewspaperIcon,
  SparklesIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface AlertSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  company: {
    companyName: string
    category: string
  }
  alerts: {
    priceAlert: boolean
    newsAlert: boolean
    impactAlert: boolean
    thresholds: {
      priceChange: number
      impactScore: number
    }
  }
  onSave: (alerts: {
    priceAlert: boolean
    newsAlert: boolean
    impactAlert: boolean
    thresholds: {
      priceChange: number
      impactScore: number
    }
  }) => void
}

export default function AlertSettingsModal({
  isOpen,
  onClose,
  company,
  alerts,
  onSave
}: AlertSettingsModalProps) {
  const [settings, setSettings] = useState(alerts)

  const handleSave = () => {
    onSave(settings)
  }

  const updateSettings = (key: string, value: boolean | number) => {
    if (key.includes('.')) {
      const [parent, child] = key.split('.')
      if (parent === 'thresholds') {
        setSettings({
          ...settings,
          thresholds: {
            ...settings.thresholds,
            [child]: value as number
          }
        })
      }
    } else {
      setSettings({
        ...settings,
        [key]: value
      })
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
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div className="bg-white dark:bg-gray-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <BellIcon className="h-6 w-6 text-electric-blue mr-2" />
                      <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900 dark:text-white">
                        알림 설정
                      </Dialog.Title>
                    </div>
                    <button
                      onClick={onClose}
                      className="rounded-md bg-white dark:bg-gray-800 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-electric-blue"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium text-gray-900 dark:text-white">{company.companyName}</span>의 알림을 설정합니다
                    </p>
                  </div>

                  <div className="space-y-6">
                    {/* 가격 변동 알림 */}
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <ChartBarIcon className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            가격 변동 알림
                          </span>
                        </div>
                        <Switch
                          checked={settings.priceAlert}
                          onChange={(checked) => updateSettings('priceAlert', checked)}
                          className={`${
                            settings.priceAlert ? 'bg-electric-blue' : 'bg-gray-200 dark:bg-gray-700'
                          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
                        >
                          <span className={`${
                            settings.priceAlert ? 'translate-x-6' : 'translate-x-1'
                          } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`} />
                        </Switch>
                      </div>
                      {settings.priceAlert && (
                        <div>
                          <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                            알림 기준 (%)
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="20"
                            value={settings.thresholds.priceChange}
                            onChange={(e) => updateSettings('thresholds.priceChange', parseInt(e.target.value))}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-800 dark:text-white"
                          />
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            ±{settings.thresholds.priceChange}% 이상 변동 시 알림
                          </p>
                        </div>
                      )}
                    </div>

                    {/* 뉴스 알림 */}
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <NewspaperIcon className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            중요 뉴스 알림
                          </span>
                        </div>
                        <Switch
                          checked={settings.newsAlert}
                          onChange={(checked) => updateSettings('newsAlert', checked)}
                          className={`${
                            settings.newsAlert ? 'bg-electric-blue' : 'bg-gray-200 dark:bg-gray-700'
                          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
                        >
                          <span className={`${
                            settings.newsAlert ? 'translate-x-6' : 'translate-x-1'
                          } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`} />
                        </Switch>
                      </div>
                      {settings.newsAlert && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          높은 영향도의 뉴스가 발생하면 알림을 받습니다
                        </p>
                      )}
                    </div>

                    {/* 영향도 알림 */}
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <SparklesIcon className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            영향도 변화 알림
                          </span>
                        </div>
                        <Switch
                          checked={settings.impactAlert}
                          onChange={(checked) => updateSettings('impactAlert', checked)}
                          className={`${
                            settings.impactAlert ? 'bg-electric-blue' : 'bg-gray-200 dark:bg-gray-700'
                          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
                        >
                          <span className={`${
                            settings.impactAlert ? 'translate-x-6' : 'translate-x-1'
                          } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`} />
                        </Switch>
                      </div>
                      {settings.impactAlert && (
                        <div>
                          <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                            알림 기준 점수
                          </label>
                          <input
                            type="range"
                            min="0.5"
                            max="1"
                            step="0.05"
                            value={settings.thresholds.impactScore}
                            onChange={(e) => updateSettings('thresholds.impactScore', parseFloat(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                          />
                          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                            <span>0.5</span>
                            <span className="font-medium text-electric-blue">
                              {settings.thresholds.impactScore.toFixed(2)}
                            </span>
                            <span>1.0</span>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            영향도가 {(settings.thresholds.impactScore * 100).toFixed(0)}% 이상일 때 알림
                          </p>
                        </div>
                      )}
                    </div>

                    {/* 알림 안내 */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                      <div className="flex">
                        <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2 flex-shrink-0" />
                        <div className="text-xs text-blue-800 dark:text-blue-200">
                          <p className="font-medium mb-1">알림 수신 방법</p>
                          <ul className="space-y-1 ml-2">
                            <li>• 이메일 알림 (가입 이메일로 발송)</li>
                            <li>• 웹 푸시 알림 (브라우저 알림 허용 필요)</li>
                            <li>• 대시보드 알림 센터</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    onClick={handleSave}
                    className="inline-flex w-full justify-center rounded-md bg-electric-blue px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 sm:ml-3 sm:w-auto"
                  >
                    저장
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-gray-800 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 sm:mt-0 sm:w-auto"
                  >
                    취소
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