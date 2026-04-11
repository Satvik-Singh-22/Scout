'use client'
import { useState, useEffect } from 'react'
import { createScheduled, updateScheduled } from '@/lib/api-client'
import type { ScheduledQuery } from '@/lib/api-client'

interface Props {
  onCreated: () => void
  onCancel: () => void
  editQuery?: ScheduledQuery | null  // If set, we're editing
}

type Frequency = 'hourly' | 'every6h' | 'daily' | 'weekly'

const DAYS_OF_WEEK = [
  { label: 'Mon', value: 1 },
  { label: 'Tue', value: 2 },
  { label: 'Wed', value: 3 },
  { label: 'Thu', value: 4 },
  { label: 'Fri', value: 5 },
  { label: 'Sat', value: 6 },
  { label: 'Sun', value: 0 },
]

function buildCronExpression(frequency: Frequency, time: string, dayOfWeek: number): string {
  const [hours, minutes] = time.split(':').map(Number)
  switch (frequency) {
    case 'hourly':
      return `${minutes} * * * *`
    case 'every6h':
      return `${minutes} */6 * * *`
    case 'daily':
      return `${minutes} ${hours} * * *`
    case 'weekly':
      return `${minutes} ${hours} * * ${dayOfWeek}`
    default:
      return `${minutes} ${hours} * * *`
  }
}

/** Parse an existing cron expression into frequency/time/dayOfWeek */
function parseCronExpression(cron: string): { frequency: Frequency; time: string; dayOfWeek: number } {
  const parts = cron.trim().split(/\s+/)
  if (parts.length < 5) return { frequency: 'daily', time: '08:00', dayOfWeek: 1 }

  const [minute, hour, , , dow] = parts

  // Hourly: "N * * * *"
  if (hour === '*' && minute !== '*') {
    return { frequency: 'hourly', time: `00:${minute.padStart(2, '0')}`, dayOfWeek: 1 }
  }

  // Every 6 hours: "N */6 * * *"
  if (hour.startsWith('*/')) {
    return { frequency: 'every6h', time: `00:${minute.padStart(2, '0')}`, dayOfWeek: 1 }
  }

  // Weekly: "N H * * D"
  if (dow !== '*' && hour !== '*') {
    return {
      frequency: 'weekly',
      time: `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`,
      dayOfWeek: parseInt(dow) || 1
    }
  }

  // Daily: "N H * * *"
  if (hour !== '*') {
    return {
      frequency: 'daily',
      time: `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`,
      dayOfWeek: 1
    }
  }

  return { frequency: 'daily', time: '08:00', dayOfWeek: 1 }
}

export default function ScheduledQueryForm({ onCreated, onCancel, editQuery }: Props) {
  const isEditing = !!editQuery

  // Parse edit data if editing
  const parsed = editQuery ? parseCronExpression(editQuery.cron_expression) : null

  const [queryText, setQueryText] = useState(editQuery?.query_text || '')
  const [frequency, setFrequency] = useState<Frequency>(parsed?.frequency || 'daily')
  const [time, setTime] = useState(parsed?.time || '08:00')
  const [dayOfWeek, setDayOfWeek] = useState(parsed?.dayOfWeek || 1)
  const [delivery, setDelivery] = useState<'EMAIL' | 'DASHBOARD'>((editQuery?.delivery as 'EMAIL' | 'DASHBOARD') || 'DASHBOARD')
  const [deliveryEmail, setDeliveryEmail] = useState('')
  const [alertCondition, setAlertCondition] = useState(editQuery?.alert_condition || '')
  const [alertSeverity, setAlertSeverity] = useState<'HIGH' | 'MEDIUM' | 'LOW'>((editQuery?.alert_severity as 'HIGH' | 'MEDIUM' | 'LOW') || 'MEDIUM')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Sync state when editQuery changes
  useEffect(() => {
    if (editQuery) {
      const p = parseCronExpression(editQuery.cron_expression)
      setQueryText(editQuery.query_text)
      setFrequency(p.frequency)
      setTime(p.time)
      setDayOfWeek(p.dayOfWeek)
      setDelivery((editQuery.delivery as 'EMAIL' | 'DASHBOARD') || 'DASHBOARD')
      setAlertCondition(editQuery.alert_condition || '')
      setAlertSeverity((editQuery.alert_severity as 'HIGH' | 'MEDIUM' | 'LOW') || 'MEDIUM')
    }
  }, [editQuery])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return
    setSaving(true)
    setError('')
    try {
      const cronExpression = buildCronExpression(frequency, time, dayOfWeek)
      const payload = {
        query_text: queryText.trim(),
        cron_expression: cronExpression,
        delivery,
        ...(delivery === 'EMAIL' && deliveryEmail ? { delivery_email: deliveryEmail } : {}),
        alert_condition: alertCondition.trim() || '',
        alert_severity: alertCondition.trim() ? alertSeverity : 'MEDIUM',
      }

      if (isEditing) {
        await updateScheduled(editQuery.id, payload)
      } else {
        await createScheduled(payload)
      }
      onCreated()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError(isEditing ? 'Failed to update scheduled query' : 'Failed to create scheduled query')
      }
    } finally {
      setSaving(false)
    }
  }

  const frequencyOptions: { label: string; value: Frequency; desc: string }[] = [
    { label: 'Hourly', value: 'hourly', desc: 'Runs every hour' },
    { label: 'Every 6 Hours', value: 'every6h', desc: 'Runs 4 times a day' },
    { label: 'Daily', value: 'daily', desc: 'Runs once a day' },
    { label: 'Weekly', value: 'weekly', desc: 'Runs once a week' },
  ]

  const getScheduleSummary = () => {
    const [h, m] = time.split(':').map(Number)
    const timeStr = new Date(0, 0, 0, h, m).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const dayName = DAYS_OF_WEEK.find(d => d.value === dayOfWeek)?.label || ''
    switch (frequency) {
      case 'hourly': return `Every hour at :${m.toString().padStart(2, '0')}`
      case 'every6h': return `Every 6 hours at :${m.toString().padStart(2, '0')} past the hour`
      case 'daily': return `Every day at ${timeStr}`
      case 'weekly': return `Every ${dayName} at ${timeStr}`
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-bold text-gray-900 mb-1">
        {isEditing ? 'Edit Scheduled Query' : 'Schedule a New Query'}
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        {isEditing ? 'Modify your scheduled query settings.' : 'Set up automated data reports delivered on your schedule.'}
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Query text */}
        <div>
          <label htmlFor="sq-query" className="block text-sm font-medium text-gray-700 mb-1.5">
            Query / Question
          </label>
          <textarea
            id="sq-query"
            rows={3}
            required
            placeholder="e.g. What is the daily failure rate for the last 7 days?"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            value={queryText}
            onChange={e => setQueryText(e.target.value)}
          />
        </div>

        {/* Schedule — Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">How often?</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
            {frequencyOptions.map(opt => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setFrequency(opt.value)}
                className={`px-3 py-2.5 rounded-lg text-left transition-all border ${
                  frequency === opt.value
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-700 ring-2 ring-indigo-500'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <span className={`block text-sm font-medium ${frequency === opt.value ? 'text-indigo-700' : 'text-gray-700'}`}>
                  {opt.label}
                </span>
                <span className={`block text-xs mt-0.5 ${frequency === opt.value ? 'text-indigo-500' : 'text-gray-400'}`}>
                  {opt.desc}
                </span>
              </button>
            ))}
          </div>

          {/* Day of week selector (only for weekly) */}
          {frequency === 'weekly' && (
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-500 mb-2">Day of week</label>
              <div className="flex gap-1.5">
                {DAYS_OF_WEEK.map(day => (
                  <button
                    key={day.value}
                    type="button"
                    onClick={() => setDayOfWeek(day.value)}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all border ${
                      dayOfWeek === day.value
                        ? 'bg-indigo-600 border-indigo-600 text-white shadow-sm'
                        : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Time picker (shown for daily and weekly) */}
          {(frequency === 'daily' || frequency === 'weekly') && (
            <div>
              <label htmlFor="sq-time" className="block text-xs font-medium text-gray-500 mb-1">
                At what time?
              </label>
              <input
                id="sq-time"
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                className="w-full sm:w-48 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {/* Minute picker for hourly */}
          {(frequency === 'hourly' || frequency === 'every6h') && (
            <div>
              <label htmlFor="sq-minute" className="block text-xs font-medium text-gray-500 mb-1">
                At what minute past the hour?
              </label>
              <input
                id="sq-minute"
                type="number"
                min={0}
                max={59}
                value={parseInt(time.split(':')[1] || '0')}
                onChange={e => setTime(`00:${e.target.value.padStart(2, '0')}`)}
                className="w-full sm:w-32 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {/* Schedule summary */}
          <div className="mt-3 flex items-center gap-2 text-xs text-indigo-600 bg-indigo-50 px-3 py-2 rounded-lg">
            <span className="material-symbols-outlined text-sm">schedule</span>
            <span className="font-medium">{getScheduleSummary()}</span>
          </div>
        </div>

        {/* Delivery method */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Method</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setDelivery('DASHBOARD')}
              className={`p-3 rounded-lg border text-left transition-all ${
                delivery === 'DASHBOARD'
                  ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500'
                  : 'bg-white border-gray-200 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">dashboard</span>
                <span>
                  <span className={`block text-sm font-medium ${delivery === 'DASHBOARD' ? 'text-indigo-700' : 'text-gray-700'}`}>
                    Dashboard
                  </span>
                  <span className={`block text-xs ${delivery === 'DASHBOARD' ? 'text-indigo-500' : 'text-gray-400'}`}>
                    Pinned to your dashboard
                  </span>
                </span>
              </span>
            </button>
            <button
              type="button"
              onClick={() => setDelivery('EMAIL')}
              className={`p-3 rounded-lg border text-left transition-all ${
                delivery === 'EMAIL'
                  ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500'
                  : 'bg-white border-gray-200 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">email</span>
                <span>
                  <span className={`block text-sm font-medium ${delivery === 'EMAIL' ? 'text-indigo-700' : 'text-gray-700'}`}>
                    Email
                  </span>
                  <span className={`block text-xs ${delivery === 'EMAIL' ? 'text-indigo-500' : 'text-gray-400'}`}>
                    Delivered to your inbox
                  </span>
                </span>
              </span>
            </button>
          </div>

          {delivery === 'EMAIL' && (
            <div className="mt-3">
              <input
                type="email"
                placeholder="your-email@company.com"
                value={deliveryEmail}
                onChange={e => setDeliveryEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}
        </div>

        {/* Alert Condition */}
        <div className="border border-amber-200 bg-amber-50/50 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="material-symbols-outlined text-amber-600 text-lg">notifications_active</span>
            <div>
              <span className="block text-sm font-medium text-gray-800">Alert Condition</span>
              <span className="block text-xs text-gray-500">Optional — Get notified when a condition is met</span>
            </div>
          </div>

          <textarea
            id="sq-alert-condition"
            rows={2}
            placeholder="e.g. Alert me if the failure rate exceeds 5%, or if total revenue drops below 10,000"
            className="w-full px-4 py-2.5 border border-amber-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-amber-400 resize-none bg-white"
            value={alertCondition}
            onChange={e => setAlertCondition(e.target.value)}
          />

          {alertCondition.trim() && (
            <div className="mt-3">
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Alert Severity</label>
              <div className="flex gap-2">
                {(['HIGH', 'MEDIUM', 'LOW'] as const).map(sev => (
                  <button
                    key={sev}
                    type="button"
                    onClick={() => setAlertSeverity(sev)}
                    className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all border ${
                      alertSeverity === sev
                        ? sev === 'HIGH'
                          ? 'bg-red-50 border-red-300 text-red-700 ring-2 ring-red-400'
                          : sev === 'MEDIUM'
                          ? 'bg-amber-50 border-amber-300 text-amber-700 ring-2 ring-amber-400'
                          : 'bg-green-50 border-green-300 text-green-700 ring-2 ring-green-400'
                        : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300'
                    }`}
                  >
                    <span className="flex items-center justify-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${
                        sev === 'HIGH' ? 'bg-red-500' : sev === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500'
                      }`} />
                      {sev === 'HIGH' ? 'High' : sev === 'MEDIUM' ? 'Medium' : 'Low'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="mt-2 text-xs text-gray-400">
            After each run, AI evaluates the result against your condition and triggers an alert if met.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={saving || !queryText.trim()}
            className="px-6 py-2.5 bg-indigo-600 text-white font-medium text-sm rounded-lg hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {saving
              ? (isEditing ? 'Saving…' : 'Creating…')
              : (isEditing ? 'Save Changes' : 'Create Schedule')
            }
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2.5 text-gray-600 font-medium text-sm rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
