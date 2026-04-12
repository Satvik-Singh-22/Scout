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

export default function OnboardingConnectPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dbType, setDbType] = useState('postgres')
  const [form, setForm] = useState({
    host: 'db.enterprise-cluster.com',
    port: '5432',
    dbName: 'analytics_prod_v2',
    schema: 'public, core_marketing',
    username: 'scout_svc_user',
    password: 'password123'
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
        connection_string: connectionString
      })
      // Save ID to local storage or state if needed, but per backend usually scans by connection ID. We'll pass it via search params.
      router.push(`/onboarding/scan?connection_id=${res.id || 'demo-conn-1'}`)
    } catch (err: any) {
      setError(err.message || 'Failed to connect to database')
    }
    setLoading(false)
  }

  return (
    <div className="flex-1 bg-surface flex items-center justify-center p-8 min-h-[calc(100vh-64px)] w-full">
      <div className="max-w-2xl w-full">
        {/* Progress Tracker */}
        <div className="mb-12">
          <div className="flex items-center justify-between relative z-10">
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm shadow-md ring-4 ring-white">1</div>
              <span className="text-xs font-bold text-gray-900">Connect DB</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-surface-container-high text-gray-400 flex items-center justify-center font-bold text-sm ring-4 ring-white">2</div>
              <span className="text-xs font-bold text-gray-400">Scan Tables</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-surface-container-high text-gray-400 flex items-center justify-center font-bold text-sm ring-4 ring-white">3</div>
              <span className="text-xs font-bold text-gray-400">Review &amp; Sync</span>
            </div>
            {/* Connecting Line */}
            <div className="absolute top-4 left-0 right-0 h-[2px] bg-surface-container-high -z-10">
              <div className="h-full bg-primary w-0 transition-all duration-1000"></div>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-surface-container-lowest rounded-2xl shadow-xl shadow-gray-200/50 overflow-hidden border border-gray-100">
          <div className="p-8 border-b border-gray-100">
            <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight leading-tight">Connect your Enterprise Datahub</h2>
            <p className="text-gray-500 mt-2 text-sm leading-relaxed max-w-lg">Scout needs read-only access to your central database to build semantic search capabilities.</p>
          </div>

          <div className="p-8 bg-gray-50/50">
            {/* Options grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <button onClick={() => setDbType('postgres')} className={`flex flex-col items-center justify-center gap-3 p-4 bg-white border-2 rounded-xl shadow-sm transition-all relative overflow-hidden group ${dbType === 'postgres' ? 'border-primary text-primary' : 'border-gray-200 text-gray-500 hover:border-indigo-300'}`}>
                {dbType === 'postgres' && (
                  <div className="absolute top-2 right-2 flex w-4 h-4 bg-primary text-white rounded-full items-center justify-center">
                    <span className="material-symbols-outlined text-[10px] font-bold">check</span>
                  </div>
                )}
                <img src="https://upload.wikimedia.org/wikipedia/commons/2/29/Postgresql_elephant.svg" className={`w-8 h-8 transition-transform ${dbType === 'postgres' ? 'scale-110' : 'group-hover:scale-110 opacity-70'}`} alt="PostgreSQL" />
                <span className="text-xs font-bold">PostgreSQL</span>
              </button>
              <button onClick={() => setDbType('snowflake')} className={`flex flex-col items-center justify-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all ${dbType === 'snowflake' ? 'border-primary text-primary border-2' : 'border-gray-200 text-gray-500'}`}>
                <img src="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg" className={`w-8 h-8 transition-opacity ${dbType === 'snowflake' ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`} alt="Snowflake" />
                <span className="text-xs font-bold">Snowflake</span>
              </button>
              <button onClick={() => setDbType('mysql')} className={`flex flex-col items-center justify-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all ${dbType === 'mysql' ? 'border-primary text-primary border-2' : 'border-gray-200 text-gray-500'}`}>
                <img src="https://upload.wikimedia.org/wikipedia/en/6/62/MySQL.svg" className={`w-8 h-8 transition-opacity ${dbType === 'mysql' ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`} alt="MySQL" />
                <span className="text-xs font-bold">MySQL</span>
              </button>
              <button onClick={() => setDbType('bigquery')} className={`flex flex-col items-center justify-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all ${dbType === 'bigquery' ? 'border-primary text-primary border-2' : 'border-gray-200 text-gray-500'}`}>
                <span className={`material-symbols-outlined text-4xl ${dbType === 'bigquery' ? 'opacity-100 text-primary' : 'opacity-70 text-gray-500'}`}>database</span>
                <span className="text-xs font-bold">BigQuery</span>
              </button>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm border border-red-100 flex items-center gap-2">
                <span className="material-symbols-outlined">error</span>
                {error}
              </div>
            )}

            <form className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-2">Host</label>
                  <input name="host" value={form.host} onChange={handleChange} type="text" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm" placeholder="db.company.com" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-2">Port</label>
                  <input name="port" value={form.port} onChange={handleChange} type="text" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm" placeholder="5432" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-2">Database Name</label>
                  <input name="dbName" value={form.dbName} onChange={handleChange} type="text" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm" placeholder="main_db" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-2">Schema</label>
                  <input name="schema" value={form.schema} onChange={handleChange} type="text" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm" placeholder="public" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-2">Username (Read-Only required)</label>
                <input name="username" value={form.username} onChange={handleChange} type="text" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm" placeholder="scout_ro_user" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-widest mb-0">Password</label>
                  <span className="text-[10px] text-primary font-bold cursor-pointer hover:underline">Use AWS Secrets EXECUTIVE instead?</span>
                </div>
                <input name="password" value={form.password} onChange={handleChange} type="password" className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary transition-all outline-none bg-white shadow-sm font-mono" />
              </div>
            </form>

            <div className="mt-8 flex items-center gap-3 p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
              <span className="material-symbols-outlined text-blue-500">lock</span>
              <p className="text-xs text-blue-700 leading-relaxed font-medium">Your credentials are encrypted at rest using AES-256. Connections are strictly enforced via TLS 1.3.</p>
            </div>
          </div>

          <div className="p-6 border-t border-gray-100 bg-white flex justify-between items-center">
            <button className="text-gray-500 text-sm font-bold px-4 py-2 hover:bg-gray-50 rounded-lg transition-colors">Cancel</button>
            <button onClick={handleConnect} disabled={loading} className="bg-primary text-white font-bold px-8 py-3 rounded-lg shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all flex items-center gap-2 disabled:opacity-50">
              {loading ? 'Connecting...' : 'Test Connection & Continue'} <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
