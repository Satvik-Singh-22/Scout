/**
 * Copyright 2026 The SCOUT Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
