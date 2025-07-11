'use client'

import { useState } from 'react'
import { CheckIcon } from '@heroicons/react/20/solid'

const tiers = [
  {
    name: '무료',
    id: 'free',
    href: '/signup',
    priceMonthly: '₩0',
    description: '개인 투자자를 위한 기본 기능',
    features: [
      '일일 AI 분석 3회',
      '관심 기업 3개 등록',
      '기본 뉴스 피드',
      '24시간 지연 알림',
      '기본 대시보드'
    ],
    featured: false
  },
  {
    name: '프리미엄',
    id: 'premium',
    href: '/signup?plan=premium',
    priceMonthly: '₩9,900',
    description: '적극적인 투자자를 위한 전체 기능',
    features: [
      '무제한 AI 분석',
      '관심 기업 50개 등록',
      '실시간 뉴스 피드',
      '즉시 알림 (이메일, 웹)',
      '고급 대시보드 & 분석',
      '기업 네트워크 전체 접근',
      'API 접근 (월 1,000회)',
      '우선 고객 지원'
    ],
    featured: true
  }
]

export default function PricingSection() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')

  return (
    <section className="py-24 bg-gray-50 dark:bg-gray-800">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-base font-semibold leading-7 text-electric-blue">가격</h2>
          <p className="mt-2 text-4xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-5xl">
            투자 스타일에 맞는 플랜 선택
          </p>
        </div>
        <p className="mx-auto mt-6 max-w-2xl text-center text-lg leading-8 text-gray-600 dark:text-gray-300">
          무료로 시작하고 필요에 따라 업그레이드하세요. 언제든 취소 가능합니다.
        </p>

        <div className="mt-16 flex justify-center">
          <div className="flex rounded-full bg-white dark:bg-gray-700 p-1 shadow-sm">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`rounded-full px-6 py-2 text-sm font-medium transition-colors ${
                billingPeriod === 'monthly'
                  ? 'bg-electric-blue text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              월간 결제
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`rounded-full px-6 py-2 text-sm font-medium transition-colors ${
                billingPeriod === 'yearly'
                  ? 'bg-electric-blue text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              연간 결제
              <span className="ml-1 text-xs">(20% 할인)</span>
            </button>
          </div>
        </div>

        <div className="isolate mx-auto mt-10 grid max-w-md grid-cols-1 gap-8 lg:mx-0 lg:max-w-none lg:grid-cols-2">
          {tiers.map((tier) => (
            <div
              key={tier.id}
              className={`rounded-3xl p-8 xl:p-10 ${
                tier.featured
                  ? 'bg-gray-900 dark:bg-gray-950 ring-2 ring-electric-blue'
                  : 'bg-white dark:bg-gray-900 ring-1 ring-gray-200 dark:ring-gray-700'
              }`}
            >
              <div className="flex items-center justify-between gap-x-4">
                <h3
                  className={`text-lg font-semibold leading-8 ${
                    tier.featured ? 'text-white' : 'text-gray-900 dark:text-white'
                  }`}
                >
                  {tier.name}
                </h3>
                {tier.featured && (
                  <p className="rounded-full bg-electric-blue px-2.5 py-1 text-xs font-semibold leading-5 text-white">
                    인기
                  </p>
                )}
              </div>
              <p className={`mt-4 text-sm leading-6 ${tier.featured ? 'text-gray-300' : 'text-gray-600 dark:text-gray-300'}`}>
                {tier.description}
              </p>
              <p className="mt-6 flex items-baseline gap-x-1">
                <span className={`text-4xl font-bold tracking-tight ${tier.featured ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                  {billingPeriod === 'yearly' && tier.priceMonthly !== '₩0' 
                    ? `₩${Math.floor(9900 * 0.8).toLocaleString()}` 
                    : tier.priceMonthly}
                </span>
                <span className={`text-sm font-semibold leading-6 ${tier.featured ? 'text-gray-300' : 'text-gray-600 dark:text-gray-300'}`}>
                  /월
                </span>
              </p>
              {billingPeriod === 'yearly' && tier.priceMonthly !== '₩0' && (
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  연 ₩{(Math.floor(9900 * 0.8) * 12).toLocaleString()} 청구
                </p>
              )}
              <a
                href={tier.href}
                className={`mt-6 block rounded-md px-3 py-2 text-center text-sm font-semibold leading-6 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${
                  tier.featured
                    ? 'bg-electric-blue text-white hover:bg-blue-600 focus-visible:outline-electric-blue'
                    : 'bg-white dark:bg-gray-800 text-electric-blue ring-1 ring-inset ring-electric-blue hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-electric-blue'
                }`}
              >
                {tier.featured ? '프리미엄 시작하기' : '무료로 시작하기'}
              </a>
              <ul className={`mt-8 space-y-3 text-sm leading-6 ${tier.featured ? 'text-gray-300' : 'text-gray-600 dark:text-gray-300'}`}>
                {tier.features.map((feature) => (
                  <li key={feature} className="flex gap-x-3">
                    <CheckIcon
                      className={`h-6 w-5 flex-none ${tier.featured ? 'text-electric-blue' : 'text-electric-blue'}`}
                      aria-hidden="true"
                    />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            모든 플랜은 VAT 포함 가격입니다. 기업 고객을 위한 맞춤 플랜이 필요하신가요?{' '}
            <a href="/contact" className="font-semibold text-electric-blue hover:text-blue-600">
              문의하기
            </a>
          </p>
        </div>
      </div>
    </section>
  )
}