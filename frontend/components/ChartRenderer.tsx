'use client'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts'

export type ChartType = 'BAR' | 'LINE' | 'PIE' | 'TABLE'

interface Props {
  chartType: ChartType
  sqlResults: any[]
  height?: number | string
  hideTable?: boolean
}

export default function ChartRenderer({ 
  chartType, 
  sqlResults, 
  height = 200,
  hideTable = false 
}: Props) {
  // Extrapolate data from SQL results for recharts
  const rawData = sqlResults || []
  let chartData: any[] = []

  if (rawData.length > 0) {
    chartData = rawData.map((row: any, i: number) => {
      const keys = Object.keys(row)
      // Heuristic: find first string for label, first number for value
      const labelKey = keys.find(k => typeof row[k] === 'string') || keys[0]
      const valueKey = keys.find(k => typeof row[k] === 'number') || keys[keys.length - 1]
      
      return {
        name: String(row[labelKey] || `Item ${i}`),
        value: Number(row[valueKey] || 0),
      }
    })
  }

  if (chartData.length === 0 && chartType !== 'TABLE') {
      return (
          <div className="flex items-center justify-center p-4 text-xs text-gray-400 italic">
              No data available for visualization.
          </div>
      )
  }

  const renderChart = () => {
    switch (chartType) {
      case 'BAR':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
                cursor={{ fill: '#F3F4F6' }} 
              />
              <Bar dataKey="value" fill="#4F46E5" radius={[4, 4, 0, 0]} barSize={32} />
            </BarChart>
          </ResponsiveContainer>
        )
      case 'LINE':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
              <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#10B981" 
                strokeWidth={3} 
                dot={{ r: 4, fill: '#10B981', strokeWidth: 2, stroke: '#fff' }} 
                activeDot={{ r: 6 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        )
      case 'PIE':
        const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
            </PieChart>
          </ResponsiveContainer>
        )
      case 'TABLE':
      default:
        if (hideTable) return null
        return (
          <div className="overflow-x-auto max-h-[300px]">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium sticky top-0">
                <tr>
                  <th className="py-2 px-3">Item</th>
                  <th className="py-2 px-3 text-right">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {chartData.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="py-2 px-3 font-medium text-gray-900">{row.name}</td>
                    <td className="py-2 px-3 text-right text-gray-600">{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
    }
  }

  return (
    <div className="w-full relative">
      {renderChart()}
    </div>
  )
}
