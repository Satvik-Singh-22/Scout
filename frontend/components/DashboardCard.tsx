'use client'
import type { DashboardCard as DashboardCardType } from '@/lib/api-client'
import ChartRenderer from './ChartRenderer'

export default function DashboardCard({ card }: { card: DashboardCardType }) {
  const chartType = card.chart_type
  const sqlResults = card.query_result?.sql_results || []

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 truncate pr-2">{card.title}</h3>
        <span className="text-[10px] uppercase font-bold text-gray-500 bg-gray-100 px-2 py-0.5 rounded tracking-wide shrink-0">
          {chartType}
        </span>
      </div>

      <div className="flex-1 w-full relative min-h-[200px]">
        <ChartRenderer 
          chartType={chartType} 
          sqlResults={sqlResults} 
          height={200}
        />
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
          {card.query_result?.answer || 'Visualization derived from enterprise data subset.'}
        </p>
      </div>
    </div>
  )
}
