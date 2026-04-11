'use client'
import { useState } from 'react'
import { createScheduled } from '@/lib/api-client'

interface Props {
  onCreated: () => void
  onCancel: () => void
}

const cronPresets = [
  { label: 'Every morning at 8 AM', value: '0 8 * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at noon', value: '0 12 * * *' },
  { label: 'Custom', value: '' },
]

export default function ScheduledQueryForm({ onCreated, onCancel }: Props) {
  const [queryText, setQueryText] = useState('')
  const [cronExpression, setCronExpression] = useState('0 8 * * *')
  const [delivery, setDelivery] = useState<'EMAIL' | 'DASHBOARD'>('DASHBOARD')
  const [deliveryEmail, setDeliveryEmail] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [selectedPreset, setSelectedPreset] = useState('0 8 * * *')

  const handlePresetChange = (value: string) => {
    setSelectedPreset(value)
    if (value) setCronExpression(value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return
    setSaving(true)
    setError('')
    try {
      await createScheduled({
        query_text: queryText.trim(),
        cron_expression: cronExpression,
        delivery,
        ...(delivery === 'EMAIL' && deliveryEmail ? { delivery_email: deliveryEmail } : {}),
      })
      onCreated()
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to create scheduled query')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-bold text-gray-900 mb-1">Schedule a New Query</h2>
      <p className="text-sm text-gray-500 mb-6">Set up automated data reports delivered on your schedule.</p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
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

        {/* Schedule preset */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Schedule</label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
            {cronPresets.map(preset => (
              <button
                key={preset.value}
                type="button"
                onClick={() => handlePresetChange(preset.value)}
                className={`px-3 py-2 rounded-lg text-xs font-medium text-left transition-all border ${
                  selectedPreset === preset.value
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-700 ring-2 ring-indigo-500'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <div>
            <label htmlFor="sq-cron" className="block text-xs font-medium text-gray-500 mb-1">
              Cron Expression
            </label>
            <input
              id="sq-cron"
              type="text"
              value={cronExpression}
              onChange={e => {
                setCronExpression(e.target.value)
                setSelectedPreset('')
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm font-mono text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
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

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={saving || !queryText.trim()}
            className="px-6 py-2.5 bg-indigo-600 text-white font-medium text-sm rounded-lg hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {saving ? 'Creating…' : 'Create Schedule'}
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
