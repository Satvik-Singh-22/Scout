'use client'
import { useState, useEffect } from 'react'
import { getAlerts, markAlertRead } from '@/lib/api-client'
import type { Alert } from '@/lib/api-client'

const severityConfig = {
  HIGH: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    badge: 'bg-red-100 text-red-700',
    dot: 'bg-red-500',
    icon: '🔴',
  },
  MEDIUM: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    badge: 'bg-orange-100 text-orange-700',
    dot: 'bg-orange-500',
    icon: '🟡',
  },
  LOW: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
    dot: 'bg-blue-500',
    icon: '🔵',
  },
}

export default function AlertCenter() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL')

  useEffect(() => {
    getAlerts()
      .then(data => {
        setAlerts(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const handleMarkRead = async (alertId: string) => {
    await markAlertRead(alertId)
    setAlerts(prev => prev.map(a => (a.id === alertId ? { ...a, is_read: true } : a)))
  }

  const handleMarkAllRead = async () => {
    const unread = alerts.filter(a => !a.is_read)
    for (const alert of unread) {
      await markAlertRead(alert.id)
    }
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))
  }

  const filteredAlerts = filter === 'ALL' ? alerts : alerts.filter(a => a.severity === filter)
  const unreadCount = alerts.filter(a => !a.is_read).length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-gray-400">
          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading alerts…
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
            <span className="material-symbols-outlined text-indigo-600">notifications_active</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Alert Center</h1>
            <p className="text-sm text-gray-500">
              {unreadCount > 0 ? `${unreadCount} unread alert${unreadCount !== 1 ? 's' : ''}` : 'All caught up'}
            </p>
          </div>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors border border-indigo-100"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Severity filter chips */}
      <div className="flex items-center gap-2 mb-6">
        {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(level => {
          const count = level === 'ALL' ? alerts.length : alerts.filter(a => a.severity === level).length
          return (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === level
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
              }`}
            >
              {level === 'ALL' ? 'All' : level.charAt(0) + level.slice(1).toLowerCase()}
              <span className={`ml-1.5 ${filter === level ? 'text-gray-300' : 'text-gray-400'}`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Alert cards */}
      {filteredAlerts.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">
          <div className="w-16 h-16 mx-auto bg-gray-50 rounded-full flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-gray-300 text-3xl">notifications_off</span>
          </div>
          <p className="text-gray-500 font-medium">No alerts to display</p>
          <p className="text-sm text-gray-400 mt-1">Check back later for new notifications</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map(alert => {
            const config = severityConfig[alert.severity]
            const timeAgo = getTimeAgo(alert.created_at)
            return (
              <div
                key={alert.id}
                className={`group bg-white border rounded-xl p-5 shadow-sm transition-all hover:shadow-md ${
                  alert.is_read ? 'border-gray-100 opacity-70' : `border-l-4 ${config.border}`
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    {/* Severity indicator */}
                    <div className={`mt-0.5 flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${config.bg}`}>
                      <span className={`w-2.5 h-2.5 rounded-full ${config.dot}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className={`text-sm font-semibold ${alert.is_read ? 'text-gray-500' : 'text-gray-900'}`}>
                          {alert.title}
                        </h3>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${config.badge}`}>
                          {alert.severity}
                        </span>
                        {!alert.is_read && (
                          <span className="w-2 h-2 bg-indigo-500 rounded-full flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed">{alert.description}</p>

                      {/* Data snapshot */}
                      {alert.data_snapshot && (
                        <div className="mt-3 bg-gray-50 border border-gray-100 rounded-lg p-3">
                          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Data Snapshot</span>
                          <pre className="mt-1 text-xs text-gray-600 font-mono overflow-x-auto">
                            {JSON.stringify(alert.data_snapshot, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Footer */}
                      <div className="flex items-center gap-4 mt-3">
                        <span className="text-xs text-gray-400">{timeAgo}</span>
                        {!alert.is_read && (
                          <button
                            onClick={() => handleMarkRead(alert.id)}
                            className="text-xs text-indigo-600 font-medium hover:text-indigo-700 transition-colors"
                          >
                            Mark as read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function getTimeAgo(dateStr: string): string {
  const now = Date.now()
  const date = new Date(dateStr).getTime()
  const diffMs = now - date
  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
