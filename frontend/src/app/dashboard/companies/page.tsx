'use client'

import { useState, useCallback, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType
} from 'reactflow'
import 'reactflow/dist/style.css'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import DashboardLayout from '@/components/layout/DashboardLayout'
import CompanyNode from '@/components/network/CompanyNode'
import CompanyDetailPanel from '@/components/network/CompanyDetailPanel'
import NetworkFilters from '@/components/network/NetworkFilters'
import { 
  BuildingOfficeIcon,
  MagnifyingGlassIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon
} from '@heroicons/react/24/outline'

// 임시 기업 데이터
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'company',
    position: { x: 400, y: 100 },
    data: { 
      label: '삼성전자',
      category: '반도체',
      marketCap: '400조원',
      impactScore: 0.92,
      newsCount: 45
    }
  },
  {
    id: '2',
    type: 'company',
    position: { x: 200, y: 200 },
    data: { 
      label: 'SK하이닉스',
      category: '반도체',
      marketCap: '80조원',
      impactScore: 0.85,
      newsCount: 32
    }
  },
  {
    id: '3',
    type: 'company',
    position: { x: 600, y: 200 },
    data: { 
      label: '현대자동차',
      category: '자동차',
      marketCap: '50조원',
      impactScore: 0.78,
      newsCount: 28
    }
  },
  {
    id: '4',
    type: 'company',
    position: { x: 400, y: 300 },
    data: { 
      label: 'LG에너지솔루션',
      category: '배터리',
      marketCap: '100조원',
      impactScore: 0.88,
      newsCount: 38
    }
  },
  {
    id: '5',
    type: 'company',
    position: { x: 200, y: 400 },
    data: { 
      label: '현대로보틱스',
      category: '로보틱스',
      marketCap: '5조원',
      impactScore: 0.72,
      newsCount: 15
    }
  },
  {
    id: '6',
    type: 'company',
    position: { x: 600, y: 400 },
    data: { 
      label: '네이버',
      category: 'AI/플랫폼',
      marketCap: '60조원',
      impactScore: 0.81,
      newsCount: 22
    }
  }
]

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'smoothstep',
    animated: true,
    label: '기술 협력',
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    data: { strength: 0.8 }
  },
  {
    id: 'e1-3',
    source: '1',
    target: '3',
    type: 'smoothstep',
    label: '부품 공급',
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    data: { strength: 0.6 }
  },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
    type: 'smoothstep',
    animated: true,
    label: '배터리 공급',
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    data: { strength: 0.9 }
  },
  {
    id: 'e3-5',
    source: '3',
    target: '5',
    type: 'smoothstep',
    label: '자회사',
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    data: { strength: 1.0 }
  },
  {
    id: 'e2-6',
    source: '2',
    target: '6',
    type: 'smoothstep',
    label: 'AI 칩 공급',
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    data: { strength: 0.7 }
  }
]

const nodeTypes = {
  company: CompanyNode,
}

export default function CompaniesPage() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showLabels, setShowLabels] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const categories = ['all', '반도체', '자동차', '배터리', '로보틱스', 'AI/플랫폼']

  const filteredNodes = useMemo(() => {
    let filtered = nodes

    if (searchQuery) {
      filtered = filtered.filter(node => 
        node.data.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(node => 
        node.data.category === selectedCategory
      )
    }

    return filtered
  }, [nodes, searchQuery, selectedCategory])

  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    return edges.filter(edge => 
      nodeIds.has(edge.source) && nodeIds.has(edge.target)
    )
  }, [edges, filteredNodes])

  const handleNetworkFilterChange = (filters: {
    minImpactScore: number
    minNewsCount: number
    relationshipTypes: string[]
    showOnlyConnected: boolean
  }) => {
    // Filter implementation
    console.log('Network filters:', filters)
  }

  const handleLayoutChange = (layout: string) => {
    // Layout change implementation
    console.log('Layout:', layout)
  }

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6">
          {/* 헤더 */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
                <BuildingOfficeIcon className="h-6 w-6 mr-2" />
                기업 네트워크
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                한국 모빌리티·로보틱스 기업들의 관계도를 시각화합니다
              </p>
            </div>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-gray-400 hover:text-gray-500 transition-colors"
            >
              {isFullscreen ? (
                <ArrowsPointingInIcon className="h-6 w-6" />
              ) : (
                <ArrowsPointingOutIcon className="h-6 w-6" />
              )}
            </button>
          </div>

          {/* 네트워크 필터 */}
          <NetworkFilters
            onFilterChange={handleNetworkFilterChange}
            onLayoutChange={handleLayoutChange}
            onToggleLabels={() => setShowLabels(!showLabels)}
            showLabels={showLabels}
          />

          {/* 검색 바 */}
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="기업 검색..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-800 dark:text-white"
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-electric-blue focus:border-transparent dark:bg-gray-800 dark:text-white"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? '전체 카테고리' : cat}
                </option>
              ))}
            </select>
          </div>

          {/* 네트워크 그래프 */}
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg ${
            isFullscreen ? 'fixed inset-0 z-50' : 'h-[600px]'
          }`}>
            <ReactFlow
              nodes={filteredNodes}
              edges={filteredEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#aaa" gap={16} />
              <Controls />
              <MiniMap 
                nodeColor={(node) => {
                  switch (node.data?.category) {
                    case '반도체': return '#3B82F6'
                    case '자동차': return '#10B981'
                    case '배터리': return '#F59E0B'
                    case '로보틱스': return '#8B5CF6'
                    case 'AI/플랫폼': return '#EF4444'
                    default: return '#6B7280'
                  }
                }}
                style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                }}
              />
            </ReactFlow>
          </div>

          {/* 범례 */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">범례</h3>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">반도체</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">자동차</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">배터리</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-purple-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">로보틱스</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">AI/플랫폼</span>
              </div>
              <div className="ml-8 flex items-center">
                <div className="w-8 h-0.5 bg-gray-400 mr-2"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">관계 연결</span>
              </div>
            </div>
          </div>

          {/* 선택된 기업 상세 정보 */}
          {selectedNode && (
            <CompanyDetailPanel
              company={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}