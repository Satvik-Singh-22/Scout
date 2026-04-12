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
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createConnection } from '@/lib/api-client'

const DB_TYPES = [
  { id: 'postgres', label: 'PostgreSQL', icon: 'storage' },
  { id: 'snowflake', label: 'Snowflake', icon: 'ac_unit' },
  { id: 'mysql', label: 'MySQL', icon: 'dns' },
  { id: 'bigquery', label: 'BigQuery', icon: 'cloud' },
]

export default function OnboardingFlow() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [dbType, setDbType] = useState('postgres')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    host: '',
    port: '5432',
    dbName: '',
    username: '',
    password: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleConnect = async () => {
    setLoading(true)
    setError('')
    try {
      const connectionString = `${dbType}://${form.username}:${form.password}@${form.host}:${form.port}/${form.dbName}`
      const res = await createConnection({
        name: `${dbType}-${form.dbName}`,
        db_type: dbType,
        connection_string: connectionString,
      })
      router.push(`/onboarding/scan?connection_id=${res.id || 'demo-conn-1'}`)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to connect to database')
      }
    }
    setLoading(false)
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress steps */}
      <div className="flex items-center justify-between mb-10 relative">
        <div className="absolute top-4 left-8 right-8 h-0.5 bg-gray-200 -z-10">
          <div
            className="h-full bg-indigo-600 transition-all duration-500"
            style={{ width: step === 1 ? '0%' : step === 2 ? '50%' : '100%' }}
          />
        </div>
        {[
          { num: 1, label: 'Connect' },
          { num: 2, label: 'Scan' },
          { num: 3, label: 'Sync' },
        ].map(s => (
          <div key={s.num} className="flex flex-col items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                step >= s.num
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {step > s.num ? '✓' : s.num}
            </div>
            <span className={`text-xs font-semibold ${step >= s.num ? 'text-gray-900' : 'text-gray-400'}`}>
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {/* Step 1: Database type selection + connection form */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">Connect Your Database</h2>
          <p className="text-sm text-gray-500 mt-1">
            Scout needs read-only access to build semantic search capabilities.
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Database type selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Database Type</label>
            <div className="grid grid-cols-4 gap-3">
              {DB_TYPES.map(db => (
                <button
                  key={db.id}
                  type="button"
                  onClick={() => setDbType(db.id)}
                  className={`p-3 rounded-lg border text-center transition-all ${
                    dbType === db.id
                      ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500'
                      : 'bg-white border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className={`material-symbols-outlined text-[20px] ${
                    dbType === db.id ? 'text-indigo-600' : 'text-gray-400'
                  }`}>
                    {db.icon}
                  </span>
                  <span className={`block text-xs font-medium mt-1 ${
                    dbType === db.id ? 'text-indigo-700' : 'text-gray-600'
                  }`}>
                    {db.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}

          {/* Connection form fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">Host</label>
              <input
                name="host"
                value={form.host}
                onChange={handleChange}
                placeholder="db.company.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">Port</label>
              <input
                name="port"
                value={form.port}
                onChange={handleChange}
                placeholder="5432"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">Database Name</label>
            <input
              name="dbName"
              value={form.dbName}
              onChange={handleChange}
              placeholder="analytics_prod"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">Username</label>
              <input
                name="username"
                value={form.username}
                onChange={handleChange}
                placeholder="scout_ro_user"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">Password</label>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Security note */}
          <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
            <span className="material-symbols-outlined text-blue-500 text-[18px]">lock</span>
            <p className="text-xs text-blue-700 font-medium">
              Credentials encrypted at rest with AES-256. Connections enforced via TLS 1.3.
            </p>
          </div>
        </div>

        {/* Footer actions */}
        <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-between items-center">
          <button className="text-sm text-gray-500 font-medium hover:text-gray-700 transition-colors">
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={loading}
            className="px-6 py-2.5 bg-indigo-600 text-white font-medium text-sm rounded-lg hover:bg-indigo-700 transition-all disabled:opacity-50 shadow-sm flex items-center gap-2"
          >
            {loading ? 'Connecting…' : 'Test Connection & Continue'}
            <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  )
}
