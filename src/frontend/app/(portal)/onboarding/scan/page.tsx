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

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { scanDatabase, registerTable } from '@/lib/api-client'
import Link from 'next/link'

interface ScannedColumn {
  name: string
  type: string
}

interface ScannedTable {
  id: string
  table_name: string
  schema: string
  columns: ScannedColumn[]
}

function OnboardingScanContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const connectionId = searchParams.get('connection_id') || 'demo-conn-1'

  const [loading, setLoading] = useState(true)
  const [tables, setTables] = useState<ScannedTable[]>([])
  const [selectedTableId, setSelectedTableId] = useState<string>('')
  const [includedTables, setIncludedTables] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Attempt real scan, fallback to dummy UI structure if it fails
    scanDatabase(connectionId)
      .then((data: any) => {
        if (data && Array.isArray(data)) {
          setTables(data)
          if (data.length > 0) setSelectedTableId(data[0].id)
        } else {
          throw new Error('Fallback')
        }
      })
      .catch(() => {
        const dummyData: ScannedTable[] = [
          {
            id: 't1', table_name: 'users', schema: 'public',
            columns: [
              { name: 'id', type: 'UUID' },
              { name: 'email', type: 'VARCHAR' },
              { name: 'created_at', type: 'TIMESTAMP' },
              { name: 'password_hash', type: 'VARCHAR' }
            ]
          },
          {
            id: 't2', table_name: 'subscriptions', schema: 'public',
            columns: [
              { name: 'id', type: 'UUID' },
              { name: 'user_id', type: 'UUID' },
              { name: 'plan_id', type: 'VARCHAR' },
              { name: 'status', type: 'VARCHAR' }
            ]
          },
          {
            id: 't3', table_name: 'campaign_metrics', schema: 'marketing_data',
            columns: [
              { name: 'id', type: 'UUID' },
              { name: 'campaign_name', type: 'VARCHAR' },
              { name: 'spend', type: 'DECIMAL' },
              { name: 'clicks', type: 'INTEGER' }
            ]
          }
        ]
        setTables(dummyData)
        setSelectedTableId(dummyData[0].id)
        // Auto-include first table for demo
        setIncludedTables(new Set(['t1']))
      })
      .finally(() => setLoading(false))
  }, [connectionId])

  const toggleInclude = (id: string) => {
    setIncludedTables(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleNext = async () => {
    if (includedTables.size === 0) return
    setSaving(true)
    try {
      const selectedTbls = tables.filter(t => includedTables.has(t.id))
      for (const tbl of selectedTbls) {
        await registerTable({
          db_connection_id: connectionId,
          table_name: tbl.table_name,
          semantic_definition: `Data from ${tbl.schema}.${tbl.table_name}`,
          columns_metadata: tbl.columns
        }).catch(err => console.log('Ignored error for demo loop', err))
      }
      router.push('/dashboard')
    } catch {
      router.push('/dashboard')
    }
  }

  // Group by schema
  const schemas = tables.reduce((acc, table) => {
    if (!acc[table.schema]) acc[table.schema] = []
    acc[table.schema].push(table)
    return acc
  }, {} as Record<string, ScannedTable[]>)

  const activeTableData = tables.find(t => t.id === selectedTableId)

  if (loading) {
    return <div className="flex-1 w-full flex items-center justify-center min-h-[calc(100vh-64px)]">Scanning connection...</div>
  }

  return (
    <div className="flex-1 bg-surface flex items-center justify-center p-8 min-h-[calc(100vh-64px)] w-full">
      <div className="max-w-4xl w-full">
        {/* Progress Tracker */}
        <div className="mb-12 max-w-2xl mx-auto">
          <div className="flex items-center justify-between relative z-10">
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm shadow-md ring-4 ring-white">
                <span className="material-symbols-outlined text-sm">check</span>
              </div>
              <span className="text-xs font-bold text-gray-900">Connect DB</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm shadow-md ring-4 ring-white shadow-indigo-200">2</div>
              <span className="text-xs font-bold text-gray-900">Scan Tables</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-surface-container-high text-gray-400 flex items-center justify-center font-bold text-sm ring-4 ring-white">3</div>
              <span className="text-xs font-bold text-gray-400">Review &amp; Sync</span>
            </div>
            {/* Connecting Line */}
            <div className="absolute top-4 left-0 right-0 h-[2px] bg-surface-container-high -z-10">
              <div className="h-full bg-primary w-1/2 transition-all duration-1000"></div>
            </div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-surface-container-lowest rounded-2xl shadow-xl shadow-gray-200/50 overflow-hidden border border-gray-100 flex flex-col md:flex-row h-[600px]">
          
          {/* Sidebar */}
          <div className="w-full md:w-64 bg-gray-50 border-r border-gray-100 flex flex-col">
            <div className="p-4 border-b border-gray-100 bg-white">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">search</span>
                <input type="text" className="w-full pl-9 pr-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all" placeholder="Filter tables..."/>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-2 py-2">Schemas</div>
              
              {/* Schema grouping */}
              <div className="space-y-1">
                {Object.entries(schemas).map(([schema, schemaTables]) => (
                  <div key={schema}>
                    <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-100 rounded-md cursor-pointer group mt-1">
                      <span className="material-symbols-outlined text-[14px] text-gray-400 group-hover:text-gray-600 transition-colors">folder</span>
                      <span className="text-xs font-semibold text-gray-700">{schema}</span>
                      <span className="ml-auto text-[10px] bg-gray-200 text-gray-500 px-1.5 rounded">{schemaTables.length}</span>
                    </div>
                    <div className="pl-6 space-y-1">
                      {schemaTables.map(tbl => (
                        <div 
                           key={tbl.id}
                           onClick={() => setSelectedTableId(tbl.id)}
                           className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer font-medium transition-colors ${
                              selectedTableId === tbl.id ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-gray-100 text-gray-600'
                           }`}
                        >
                          <span className={`material-symbols-outlined text-[14px] ${selectedTableId === tbl.id ? 'text-indigo-400' : 'text-gray-400'}`}>table</span>
                          <span className="text-xs">{tbl.table_name}</span>
                          {includedTables.has(tbl.id) && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-500"></span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            {activeTableData ? (
               <>
                 <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white h-[88px] shrink-0">
                   <div>
                     <div className="flex items-center gap-2 text-xs text-gray-500 mb-1 font-mono">
                       <span>{activeTableData.schema}</span> <span className="material-symbols-outlined text-[10px]">arrow_forward_ios</span> <span className="font-bold text-primary">{activeTableData.table_name}</span>
                     </div>
                     <h3 className="text-xl font-bold text-gray-900">Table Configuration</h3>
                   </div>
                   <div className="flex items-center gap-3">
                     <label className="flex items-center gap-2 cursor-pointer" onClick={() => toggleInclude(activeTableData.id)}>
                       <span className="text-xs font-bold text-gray-700">Include in Vector Store</span>
                       <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                         <input type="checkbox" className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 border-primary appearance-none cursor-pointer transition-transform duration-200 translate-x-5" checked={includedTables.has(activeTableData.id)} readOnly/>
                         <label className={`toggle-label block overflow-hidden h-5 rounded-full cursor-pointer ${includedTables.has(activeTableData.id) ? 'bg-primary' : 'bg-gray-300'}`}></label>
                       </div>
                     </label>
                   </div>
                 </div>

                 <div className="flex-1 overflow-y-auto bg-gray-50/30">
                   <table className="w-full text-left border-collapse">
                     <thead className="bg-gray-50 border-b border-gray-100 sticky top-0 z-10">
                       <tr>
                         <th className="px-6 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest w-10">Include</th>
                         <th className="px-6 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Column Name</th>
                         <th className="px-6 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Data Type</th>
                         <th className="px-6 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest">Semantic Tag</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-gray-100">
                       {activeTableData.columns.map(col => (
                         <tr key={col.name} className={`bg-white hover:bg-gray-50 transition-colors ${col.name.includes('hash') || col.name.includes('password') ? 'opacity-60 bg-gray-50' : ''}`}>
                           <td className="px-6 py-3 text-center">
                             <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" defaultChecked={!col.name.includes('hash')} />
                           </td>
                           <td className="px-6 py-3">
                             <div className="flex items-center gap-2">
                               {col.name === 'id' ? <span className="material-symbols-outlined text-[14px] text-amber-500" title="Primary Key">key</span> : null}
                               <span className={`text-sm font-bold text-gray-900 font-mono ${col.name !== 'id' ? 'pl-5' : ''}`}>{col.name}</span>
                             </div>
                           </td>
                           <td className="px-6 py-3">
                             <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 font-mono">{col.type}</span>
                           </td>
                           <td className="px-6 py-3">
                             <select className="text-xs bg-gray-50 border border-gray-200 rounded px-2 py-1 outline-none focus:border-primary text-gray-700 w-full cursor-pointer">
                               {col.name === 'id' && <option>Identifier (Primary)</option>}
                               {col.type === 'VARCHAR' && !col.name.includes('hash') && <option>Searchable Text</option>}
                               {col.type === 'TIMESTAMP' && <option>Temporal Data</option>}
                               {col.name.includes('hash') && <option>Ignored (Security)</option>}
                               <option>Generic Attribute</option>
                             </select>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               </>
            ) : (
               <div className="flex-1 flex items-center justify-center text-gray-400">Select a table to configure</div>
            )}
            
            <div className="p-4 border-t border-gray-100 bg-white flex justify-between items-center shrink-0">
              <Link href="/onboarding" className="text-gray-500 text-sm font-bold px-4 py-2 hover:bg-gray-50 rounded-lg transition-colors">Back</Link>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 font-medium">{includedTables.size} tables selected</span>
                <button onClick={handleNext} disabled={saving || includedTables.size === 0} className="bg-primary text-white font-bold px-6 py-2.5 rounded-lg shadow-md hover:bg-indigo-700 transition-all disabled:opacity-50">
                  {saving ? 'Registering...' : 'Register Selected Tables'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function OnboardingScanPage() {
  return (
    <Suspense fallback={<div className="flex-1 w-full flex items-center justify-center min-h-[calc(100vh-64px)]">Loading...</div>}>
      <OnboardingScanContent />
    </Suspense>
  )
}
