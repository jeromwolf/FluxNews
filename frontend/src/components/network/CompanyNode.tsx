'use client'

import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import { 
  BuildingOfficeIcon,
  SparklesIcon,
  NewspaperIcon
} from '@heroicons/react/24/outline'

interface CompanyNodeProps {
  data: {
    label: string
    category: string
    marketCap: string
    impactScore: number
    newsCount: number
  }
  selected?: boolean
}

const CompanyNode = memo(({ data, selected }: CompanyNodeProps) => {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case '반도체': return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
      case '자동차': return 'border-green-500 bg-green-50 dark:bg-green-900/20'
      case '배터리': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
      case '로보틱스': return 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
      case 'AI/플랫폼': return 'border-red-500 bg-red-50 dark:bg-red-900/20'
      default: return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20'
    }
  }

  const getImpactColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600 dark:text-red-400'
    if (score >= 0.6) return 'text-orange-600 dark:text-orange-400'
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 min-w-[200px] transition-all
      ${getCategoryColor(data.category)}
      ${selected ? 'ring-2 ring-electric-blue ring-offset-2' : ''}
      hover:shadow-lg cursor-pointer
    `}>
      <Handle type="target" position={Position.Top} />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <BuildingOfficeIcon className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {data.label}
          </h3>
        </div>
      </div>

      <div className="space-y-1 text-xs">
        <div className="flex justify-between items-center">
          <span className="text-gray-600 dark:text-gray-400">{data.category}</span>
          <span className="text-gray-700 dark:text-gray-300 font-medium">
            {data.marketCap}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <SparklesIcon className={`h-4 w-4 mr-1 ${getImpactColor(data.impactScore)}`} />
            <span className={`font-medium ${getImpactColor(data.impactScore)}`}>
              {(data.impactScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center text-gray-600 dark:text-gray-400">
            <NewspaperIcon className="h-4 w-4 mr-1" />
            <span>{data.newsCount}</span>
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  )
})

CompanyNode.displayName = 'CompanyNode'

export default CompanyNode