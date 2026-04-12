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
import { useState, useEffect } from 'react'
import { getAlerts, markAlertRead } from '@/lib/api-client'
import type { Alert } from '@/lib/api-client'

export default function AlertCenter() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL')

  useEffect(() => {
    getAlerts()
      .then(data => { setAlerts(data); setLoading(false) })
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
    <div className="max-w-5xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex items-end justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
              Alert Center
            </h1>
            <span className={`px-2.5 py-0.5 text-sm font-bold rounded-full ${
              unreadCount > 0
                ? 'bg-red-100 text-red-700'
                : 'bg-green-100 text-green-700'
            }`}>
              {unreadCount > 0 ? `${unreadCount} Unread` : 'All caught up'}
            </span>
          </div>
          <p className="text-gray-500">Monitor system health and business anomalies across all data sources.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Mark all as read
          </button>
        </div>
      </div>

      {/* ── Filter chips ── */}
      <div className="flex items-center gap-2 mb-6">
        {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(level => {
          const count = level === 'ALL' ? alerts.length : alerts.filter(a => a.severity === level).length
          return (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                filter === level
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
              }`}
            >
              {level === 'ALL' ? 'All' : level.charAt(0) + level.slice(1).toLowerCase()}
              <span className={`ml-1.5 ${filter === level ? 'text-gray-400' : 'text-gray-400'}`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* ── Alert cards ── */}
      {filteredAlerts.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-16 text-center shadow-sm">
          <div className="w-16 h-16 mx-auto bg-gray-50 rounded-full flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-gray-300 text-3xl">notifications_off</span>
          </div>
          <p className="text-gray-500 font-semibold text-lg">No alerts to display</p>
          <p className="text-sm text-gray-400 mt-1">Check back later for new notifications</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredAlerts.map(alert => {
            const timeAgo = getTimeAgo(alert.created_at)
            const isRead = alert.is_read

            // Severity-specific styles — colors persist even when read
            const sev = alert.severity

            const cardBg = sev === 'HIGH' ? 'bg-[#fff5f5]'
              : sev === 'MEDIUM' ? 'bg-[#fffbeb]'
              : 'bg-white'

            const stripColor = sev === 'HIGH' ? 'bg-red-500'
              : sev === 'MEDIUM' ? 'bg-amber-500'
              : ''

            const iconColor = sev === 'HIGH' ? 'text-red-500'
              : sev === 'MEDIUM' ? 'text-amber-600'
              : 'text-indigo-500'

            const ringColor = sev === 'HIGH' ? 'ring-red-500/10'
              : sev === 'MEDIUM' ? 'ring-amber-500/10'
              : 'ring-gray-200/60'

            const badgeColor = sev === 'HIGH' ? 'text-red-600'
              : sev === 'MEDIUM' ? 'text-amber-600'
              : 'text-gray-500'

            const iconName = sev === 'HIGH' ? 'trending_down'
              : sev === 'MEDIUM' ? 'sync_problem'
              : 'info'

            return (
              <div
                key={alert.id}
                className={`group relative rounded-xl p-5 flex items-start gap-5 transition-all ring-1 overflow-hidden ${cardBg} ${ringColor} hover:shadow-lg ${
                  isRead ? 'opacity-80 hover:opacity-100' : ''
                }`}
              >
                {/* Left color strip — always visible */}
                {stripColor && (
                  <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${stripColor}`} />
                )}

                {/* Circular Icon */}
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center shadow-sm bg-white ${iconColor}`}>
                  <span className="material-symbols-outlined">{iconName}</span>
                </div>

                {/* Content */}
                <div className="flex-grow min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={`text-lg font-bold ${isRead ? 'text-gray-500' : 'text-gray-900'}`}>
                      {alert.title}
                    </h3>
                    <span className={`text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${badgeColor}`}>
                      {sev === 'HIGH' ? 'High Severity' : sev === 'MEDIUM' ? 'Medium' : 'Low'}
                    </span>
                  </div>

                  <p className={`text-sm mb-4 max-w-2xl leading-relaxed ${isRead ? 'text-gray-400' : 'text-gray-600'}`}>
                    {alert.description}
                  </p>

                  {/* Data snapshot */}
                  {alert.data_snapshot && !isRead && (
                    <div className="mb-4 bg-white/70 border border-gray-200/60 rounded-lg p-3">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Data Snapshot</span>
                      <pre className="mt-1 text-xs text-gray-600 font-mono overflow-x-auto">
                        {JSON.stringify(alert.data_snapshot, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">schedule</span>
                      {timeAgo}
                    </span>
                    {!isRead ? (
                      <>
                        <button
                          onClick={() => handleMarkRead(alert.id)}
                          className="text-xs font-bold text-indigo-600 hover:underline transition-all"
                        >
                          Mark as Read
                        </button>
                        <button className="text-xs font-bold text-gray-500 hover:text-gray-700 transition-all">
                          View Report
                        </button>
                      </>
                    ) : (
                      <span className="text-xs text-gray-400 flex items-center gap-1 italic">
                        <span className="material-symbols-outlined text-sm">done_all</span>
                        Read
                      </span>
                    )}
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
