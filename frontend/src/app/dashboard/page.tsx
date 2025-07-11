'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/components/auth/AuthProvider'

export default function DashboardPage() {
  const { user, signOut } = useAuth()

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                대시보드
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                환영합니다, {user?.email}님!
              </p>
            </div>
            <button
              onClick={signOut}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-electric-blue dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
            >
              로그아웃
            </button>
          </div>
          
          <div className="mt-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              대시보드 기능 (개발 예정)
            </h2>
            <ul className="space-y-2 text-gray-600 dark:text-gray-400">
              <li>• 실시간 뉴스 피드</li>
              <li>• AI 분석 결과</li>
              <li>• 관심 기업 목록</li>
              <li>• 영향도 점수 차트</li>
              <li>• 알림 설정</li>
            </ul>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}