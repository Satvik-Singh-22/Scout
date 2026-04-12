'use client'
import { useEffect, useState } from 'react'
import { getScheduledHistory } from '@/lib/api-client'
import { History, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function ScheduledHistoryPage({ params }: { params: { id: string } }) {
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getScheduledHistory(params.id).then(data => {
      setHistory(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [params.id])

  if (loading) return <div className="flex items-center justify-center p-12 text-gray-400">Loading history...</div>

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link href="/scheduled" className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-900">
          <ArrowLeft size={16} className="mr-1" /> Back to Scheduled Queries
        </Link>
      </div>
      
      <div className="flex items-center gap-3 mb-8">
        <History className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Execution History</h1>
          <p className="text-sm text-gray-500">Past runs for this scheduled query</p>
        </div>
      </div>
      
      {history.length === 0 ? (
        <div className="bg-white border text-center p-12 rounded-xl text-gray-500 shadow-sm">
          No execution history found.
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((h, i) => (
            <div key={i} className="bg-white p-5 rounded-xl border shadow-sm flex items-start justify-between">
              <div>
                <span className={`inline-block px-2.5 py-1 rounded text-xs font-semibold mb-2 ${
                  h.status === 'SUCCESS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {h.status}
                </span>
                <div className="text-xs text-gray-400">
                  Executed at: {new Date(h.executed_at).toLocaleString()}
                </div>
                {h.result_data && (
                  <pre className="mt-3 text-xs bg-gray-50 p-3 rounded text-gray-600 max-w-2xl overflow-auto border">
                    {JSON.stringify(h.result_data, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
