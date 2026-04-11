'use client'
import { useEffect, useState } from 'react'
import { getScheduled, toggleScheduled } from '@/lib/api-client'
import type { ScheduledQuery } from '@/lib/api-client'
import ScheduledQueryForm from '@/components/ScheduledQueryForm'
import { Clock } from 'lucide-react'
import Link from 'next/link'

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

export default function ScheduledPage() {
  const [queries, setQueries] = useState<ScheduledQuery[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  const loadQueries = () => {
    setLoading(true)
    getScheduled()
      .then(data => { setQueries(data); setLoading(false) })
      .catch(() => { setError('Failed to load scheduled queries'); setLoading(false) })
  }

  useEffect(() => { loadQueries() }, [])

  const handleToggle = async (q: ScheduledQuery) => {
    const nextState = !q.is_active
    // Optimistic update
    setQueries(prev => prev.map(x => x.id === q.id ? { ...x, is_active: nextState } : x))
    try {
      await toggleScheduled(q.id, nextState)
    } catch {
      // Revert on failure
      setQueries(prev => prev.map(x => x.id === q.id ? { ...x, is_active: q.is_active } : x))
    }
  }

  const handleCreated = () => {
    setShowForm(false)
    loadQueries()
  }

  if (loading) return (
    <div className="flex items-center justify-center p-12 text-gray-400">
      <svg className="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      Loading scheduled queries...
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Clock className="text-indigo-600" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Scheduled Queries</h1>
            <p className="text-sm text-gray-500">Automated reports and notifications</p>
          </div>
        </div>
        {/* FIX: Button now toggles the create form */}
        <button
          onClick={() => setShowForm(prev => !prev)}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-semibold text-sm shadow-sm transition-all active:scale-95"
        >
          <span className="material-symbols-outlined text-sm">{showForm ? 'close' : 'add'}</span>
          {showForm ? 'Cancel' : 'New Schedule'}
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* Create form */}
      {showForm && (
        <div className="mb-8">
          <ScheduledQueryForm
            onCreated={handleCreated}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* Empty state */}
      {queries.length === 0 && !showForm && (
        <div className="bg-white border-2 border-dashed border-gray-200 text-center p-16 rounded-xl text-gray-400">
          <Clock size={36} className="mx-auto mb-3 text-gray-300" />
          <p className="font-semibold text-gray-500 mb-1">No scheduled queries yet</p>
          <p className="text-sm mb-6">Set up recurring reports delivered to your dashboard or email</p>
          <button
            onClick={() => setShowForm(true)}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-all"
          >
            Create Your First Schedule
          </button>
        </div>
      )}

      {/* Table */}
      {queries.length > 0 && (
        <div className="overflow-hidden bg-white border border-gray-200 rounded-xl shadow-sm">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 font-semibold text-gray-500 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4">Query / Prompt</th>
                <th className="px-6 py-4">Schedule</th>
                <th className="px-6 py-4">Delivery</th>
                <th className="px-6 py-4">Last Run</th>
                <th className="px-6 py-4">Active</th>
                <th className="px-6 py-4 text-right">History</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {queries.map(q => (
                <tr key={q.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 max-w-xs">
                    <p className="font-medium text-gray-900 truncate">{q.query_text}</p>
                    {q.next_run_at && (
                      <p className="text-xs text-gray-400 mt-0.5">Next: {formatDate(q.next_run_at)}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500 font-mono text-xs">{q.cron_expression}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      q.delivery === 'EMAIL'
                        ? 'bg-blue-50 text-blue-700'
                        : 'bg-indigo-50 text-indigo-700'
                    }`}>
                      {q.delivery}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-xs">{formatDate(q.last_run_at)}</td>
                  <td className="px-6 py-4">
                    {/* Toggle switch */}
                    <button
                      onClick={() => handleToggle(q)}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
                        q.is_active ? 'bg-indigo-600' : 'bg-gray-200'
                      }`}
                      aria-label={q.is_active ? 'Disable' : 'Enable'}
                    >
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                        q.is_active ? 'translate-x-4' : 'translate-x-1'
                      }`} />
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/scheduled/${q.id}/history`}
                      className="text-indigo-600 hover:text-indigo-900 font-medium text-xs inline-flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-sm">history</span>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
