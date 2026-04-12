'use client'
import { useEffect, useState } from 'react'
import { getScheduled, toggleScheduled, deleteScheduled } from '@/lib/api-client'
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

function describeCron(cron: string): string {
  const parts = cron.trim().split(/\s+/)
  if (parts.length < 5) return cron

  const [minute, hour, , , dow] = parts

  const formatTime = (h: string, m: string): string => {
    const hh = parseInt(h)
    const mm = parseInt(m)
    if (isNaN(hh)) return ''
    const ampm = hh >= 12 ? 'PM' : 'AM'
    const displayH = hh === 0 ? 12 : hh > 12 ? hh - 12 : hh
    return `${displayH}:${mm.toString().padStart(2, '0')} ${ampm}`
  }

  if (minute === '*' && hour === '*') return 'Every minute'
  if (hour === '*' && minute !== '*') return `Hourly at :${minute.padStart(2, '0')}`
  if (hour.startsWith('*/')) {
    const interval = hour.replace('*/', '')
    return `Every ${interval} hours at :${minute.padStart(2, '0')}`
  }

  const dayNames: Record<string, string> = {
    '0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed',
    '4': 'Thu', '5': 'Fri', '6': 'Sat', '7': 'Sun'
  }

  if (dow !== '*' && hour !== '*') {
    return `Weekly on ${dayNames[dow] || dow} at ${formatTime(hour, minute)}`
  }
  if (dow === '*' && hour !== '*') {
    return `Daily at ${formatTime(hour, minute)}`
  }
  return cron
}

export default function ScheduledPage() {
  const [queries, setQueries] = useState<ScheduledQuery[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingQuery, setEditingQuery] = useState<ScheduledQuery | null>(null)
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
    setQueries(prev => prev.map(x => x.id === q.id ? { ...x, is_active: nextState } : x))
    try {
      await toggleScheduled(q.id, nextState)
    } catch {
      setQueries(prev => prev.map(x => x.id === q.id ? { ...x, is_active: q.is_active } : x))
    }
  }

  const handleCreated = () => {
    setShowForm(false)
    setEditingQuery(null)
    loadQueries()
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingQuery(null)
  }

  const handleEdit = (q: ScheduledQuery) => {
    setEditingQuery(q)
    setShowForm(true)
    // Scroll to top to show the form
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (q: ScheduledQuery) => {
    if (!confirm(`Delete scheduled query "${q.query_text.slice(0, 60)}${q.query_text.length > 60 ? '…' : ''}"? This cannot be undone.`)) return
    // Optimistic removal
    setQueries(prev => prev.filter(x => x.id !== q.id))
    try {
      await deleteScheduled(q.id)
    } catch {
      setError('Failed to delete scheduled query')
      loadQueries()
    }
  }

  const handleNewSchedule = () => {
    setEditingQuery(null)
    setShowForm(prev => !prev)
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
        <button
          onClick={handleNewSchedule}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-semibold text-sm shadow-sm transition-all active:scale-95"
        >
          <span className="material-symbols-outlined text-sm">{showForm && !editingQuery ? 'close' : 'add'}</span>
          {showForm && !editingQuery ? 'Cancel' : 'New Schedule'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {/* Create / Edit form */}
      {showForm && (
        <div className="mb-8">
          <ScheduledQueryForm
            onCreated={handleCreated}
            onCancel={handleCancel}
            editQuery={editingQuery}
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
            onClick={() => { setEditingQuery(null); setShowForm(true) }}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-all"
          >
            Create Your First Schedule
          </button>
        </div>
      )}

      {/* Table */}
      {queries.length > 0 && (
        <div className="overflow-hidden bg-white border border-gray-200 rounded-xl shadow-sm">
          <table className="w-full text-sm text-left table-fixed">
            <thead className="bg-gray-50 font-semibold text-gray-500 border-b border-gray-200 text-xs">
              <tr>
                <th className="px-3 py-3 w-[25%]">Query / Prompt</th>
                <th className="px-3 py-3 w-[14%]">Schedule</th>
                <th className="px-3 py-3 w-[8%]">Delivery</th>
                <th className="px-3 py-3 w-[15%]">Alert</th>
                <th className="px-3 py-3 w-[10%]">Last Run</th>
                <th className="px-3 py-3 w-[8%]">Active</th>
                <th className="px-3 py-3 w-[20%] text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {queries.map(q => (
                <tr key={q.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-3 py-3">
                    <p className="font-medium text-gray-900 truncate text-xs">{q.query_text}</p>
                    {q.next_run_at && (
                      <p className="text-[11px] text-gray-400 mt-0.5">Next: {formatDate(q.next_run_at)}</p>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <span className="text-gray-700 text-xs font-medium">{describeCron(q.cron_expression)}</span>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      q.delivery === 'EMAIL'
                        ? 'bg-blue-50 text-blue-700'
                        : 'bg-indigo-50 text-indigo-700'
                    }`}>
                      {q.delivery}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    {q.alert_condition ? (
                      <div className="flex items-center gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                          q.alert_severity === 'HIGH' ? 'bg-red-500'
                          : q.alert_severity === 'LOW' ? 'bg-green-500'
                          : 'bg-amber-500'
                        }`} />
                        <span className="text-[11px] text-gray-600 truncate" title={q.alert_condition}>
                          {q.alert_condition}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-gray-500 text-xs">{formatDate(q.last_run_at)}</td>
                  <td className="px-3 py-3">
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
                  <td className="px-3 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleEdit(q)}
                        className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-900 font-medium text-xs px-1.5 py-1 rounded-md hover:bg-indigo-50 transition-colors"
                        title="Edit"
                      >
                        <span className="material-symbols-outlined text-[16px]">edit</span>
                        Edit
                      </button>
                      <Link
                        href={`/scheduled/${q.id}/history`}
                        className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 font-medium text-xs px-1.5 py-1 rounded-md hover:bg-gray-100 transition-colors"
                      >
                        <span className="material-symbols-outlined text-[16px]">history</span>
                        History
                      </Link>
                      <button
                        onClick={() => handleDelete(q)}
                        className="inline-flex items-center gap-1 text-red-500 hover:text-red-700 font-medium text-xs px-1.5 py-1 rounded-md hover:bg-red-50 transition-colors"
                        title="Delete"
                      >
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                        Delete
                      </button>
                    </div>
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
