import { 
  ChartBarIcon, 
  BellAlertIcon, 
  GlobeAltIcon, 
  LanguageIcon,
  ShieldCheckIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'

const features = [
  {
    name: '실시간 AI 분석',
    description: 'GPT-4와 FinBERT를 활용하여 글로벌 뉴스가 한국 기업에 미치는 영향을 실시간으로 분석합니다.',
    icon: LightBulbIcon,
    color: 'text-electric-blue',
    bgColor: 'bg-electric-blue/10'
  },
  {
    name: '기업 네트워크 시각화',
    description: '80개 주요 기업 간의 관계를 시각화하여 숨겨진 연결고리와 파급 효과를 한눈에 파악합니다.',
    icon: GlobeAltIcon,
    color: 'text-neon-purple',
    bgColor: 'bg-neon-purple/10'
  },
  {
    name: '영향도 점수 시스템',
    description: '0-1.0 스케일의 정밀한 영향도 점수로 투자 의사결정에 필요한 정량적 데이터를 제공합니다.',
    icon: ChartBarIcon,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10'
  },
  {
    name: '맞춤형 실시간 알림',
    description: '관심 기업에 중요한 뉴스가 발생하면 즉시 알림을 받아 빠른 대응이 가능합니다.',
    icon: BellAlertIcon,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10'
  },
  {
    name: '한국어 완벽 지원',
    description: '한국 뉴스 소스와 한국어 자연어 처리로 현지 맥락을 정확히 이해합니다.',
    icon: LanguageIcon,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10'
  },
  {
    name: '엔터프라이즈급 보안',
    description: 'Supabase의 Row Level Security로 귀하의 투자 정보를 안전하게 보호합니다.',
    icon: ShieldCheckIcon,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10'
  }
]

export default function FeaturesSection() {
  return (
    <section className="py-24 bg-white dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-semibold leading-7 text-electric-blue">더 스마트한 투자</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
            AI가 제공하는 차별화된 기능
          </p>
          <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-300">
            FluxNews는 최신 AI 기술을 활용하여 투자자에게 실질적인 가치를 제공합니다
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.name} className="flex flex-col">
                <dt className="text-base font-semibold leading-7 text-gray-900 dark:text-white">
                  <div className={`mb-6 flex h-16 w-16 items-center justify-center rounded-xl ${feature.bgColor}`}>
                    <feature.icon className={`h-8 w-8 ${feature.color}`} aria-hidden="true" />
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600 dark:text-gray-300">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="mt-16 flex justify-center">
          <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-gray-600 ring-1 ring-gray-900/10 hover:ring-gray-900/20 dark:text-gray-300 dark:ring-gray-700 dark:hover:ring-gray-600">
            하루 평균 3,000개 이상의 뉴스를 분석합니다.{' '}
            <a href="/about" className="font-semibold text-electric-blue">
              <span className="absolute inset-0" aria-hidden="true" />
              자세히 알아보기 <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}