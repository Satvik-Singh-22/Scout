'use client'

import { useState, useEffect } from 'react'
import { adminGetTables, adminGetTeams, adminGetUsers, adminAssignTables, adminRevokeTable, adminUpdateUserAccess } from '@/lib/api-client'
import type { AdminTable, AdminTeam, AdminUser } from '@/lib/api-client'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'tables' | 'users'>('tables')
  const [tables, setTables] = useState<AdminTable[]>([])
  const [teams, setTeams] = useState<AdminTeam[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // Checkboxes state: {team_id: Set<table_name>}
  const [assignments, setAssignments] = useState<Record<string, Set<string>>>({})

  useEffect(() => {
    Promise.all([adminGetTables(), adminGetTeams(), adminGetUsers()])
      .then(([t, teams, users]) => {
        setTables(t)
        setTeams(teams)
        setUsers(users)
        if (teams.length > 0) setSelectedTeam(teams[0].id)

        // Build initial assignments
        const map: Record<string, Set<string>> = {}
        teams.forEach(team => {
          map[team.id] = new Set(
            t.filter(tbl =>
              tbl.team_assignments.some(a => a.team_id === team.id && a.is_active)
            ).map(tbl => tbl.table_name)
          )
        })
        setAssignments(map)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const toggleTable = (tableName: string) => {
    setAssignments(prev => {
      const teamSet = new Set(prev[selectedTeam] || [])
      if (teamSet.has(tableName)) teamSet.delete(tableName)
      else teamSet.add(tableName)
      return { ...prev, [selectedTeam]: teamSet }
    })
  }

  const saveAssignments = async () => {
    setSaving(true)
    setMessage('')
    try {
      const checkedTables = Array.from(assignments[selectedTeam] || [])

      const currentlyActive = tables.filter(t =>
        t.team_assignments.some(a => a.team_id === selectedTeam && a.is_active)
      )
      for (const t of currentlyActive) {
        if (!checkedTables.includes(t.table_name)) {
          const config = t.team_assignments.find(a => a.team_id === selectedTeam)
          if (config) await adminRevokeTable(config.config_id)
        }
      }

      const tableAssignments = checkedTables.map(name => {
        const tbl = tables.find(t => t.table_name === name)!
        return {
          table_name: name,
          semantic_definition: `Data from ${name} table.`,
          columns_metadata: []
        }
      })

      if (tableAssignments.length > 0) {
        await adminAssignTables({ team_id: selectedTeam, table_assignments: tableAssignments })
      }

      setMessage('Published cleanly.')
      const updated = await adminGetTables()
      setTables(updated)
    } catch {
      setMessage('Failed to publish rules.')
    }
    setSaving(false)
  }

  const updateUserAccess = async (userId: string, teamIds: string[]) => {
    try {
      await adminUpdateUserAccess(userId, teamIds)
      const updatedUsers = await adminGetUsers()
      setUsers(updatedUsers)
    } catch {
      // ignore
    }
  }

  const activeTeamData = teams.find(t => t.id === selectedTeam)
  const filteredTables = tables.filter(t => t.table_name.toLowerCase().includes(searchQuery.toLowerCase()))

  if (loading) return <div className="flex-1 w-full bg-background flex flex-col items-center justify-center min-h-[calc(100vh-64px)] text-gray-500 font-medium">Booting Platform Governance...</div>

  return (
    <div className="flex-1 w-full bg-background relative flex flex-col p-8 mb-4 max-w-7xl mx-auto min-h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 shrink-0">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">Governance Console</h1>
          <p className="text-gray-500 font-medium mt-1">Cross-team table assignment and permission orchestration.</p>
        </div>
        <div className="flex items-center gap-3">
          {message && <span className="text-sm font-bold text-gray-400">{message}</span>}
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 font-bold text-sm rounded-lg hover:bg-gray-50 transition-colors shadow-sm">
            <span className="material-symbols-outlined text-[18px]">history</span>
            Audit Logs
          </button>
          <button onClick={saveAssignments} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-primary text-white font-bold text-sm rounded-lg hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-200 disabled:opacity-50">
            <span className="material-symbols-outlined text-[18px]">save</span>
            {saving ? 'Publishing...' : 'Publish Rules'}
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <button onClick={() => setActiveTab('tables')} className={`px-4 py-2 text-sm font-bold rounded-lg transition-colors ${activeTab === 'tables' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>Table Allocations</button>
        <button onClick={() => setActiveTab('users')} className={`px-4 py-2 text-sm font-bold rounded-lg transition-colors ${activeTab === 'users' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>Analyst Cross-Access</button>
      </div>

      <div className="flex gap-8 flex-1 overflow-hidden min-h-0">
        {activeTab === 'tables' && (
          <>
            {/* Left Column - Team Selection */}
            <div className="w-80 flex flex-col shrink-0">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-full overflow-hidden">
                <div className="p-4 border-b border-gray-100 bg-gray-50/50">
                  <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-gray-500">groups</span>
                    Tenant Workspaces
                  </h2>
                </div>
                <div className="p-3 flex flex-col flex-1 min-h-0">
                  <div className="space-y-1 overflow-y-auto pr-1 flex-1">
                    {teams.map((team) => (
                      <div 
                        key={team.id}
                        onClick={() => setSelectedTeam(team.id)}
                        className={`flex items-center justify-between p-3 rounded-lg border-2 cursor-pointer transition-colors group ${selectedTeam === team.id ? 'border-primary bg-indigo-50/50' : 'border-transparent hover:bg-gray-50'}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded flex items-center justify-center font-bold text-xs ring-1 ${selectedTeam === team.id ? 'bg-indigo-100 text-indigo-700 ring-indigo-200' : 'bg-gray-100 text-gray-600 ring-transparent'}`}>
                            {team.name.substring(0,2).toUpperCase()}
                          </div>
                          <div>
                            <div className={`text-sm font-bold ${selectedTeam === team.id ? 'text-indigo-900' : 'text-gray-700'}`}>{team.name.split('—')[0]?.trim()}</div>
                            <div className={`text-[10px] font-semibold uppercase tracking-wider ${selectedTeam === team.id ? 'text-indigo-600' : 'text-gray-500'}`}>
                              {team.table_count || assignments[team.id]?.size || 0} Tables assigned
                            </div>
                          </div>
                        </div>
                        {selectedTeam === team.id && <span className="material-symbols-outlined text-primary text-[18px]">chevron_right</span>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Table Allocation */}
            <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col overflow-hidden min-h-0">
              <div className="p-6 border-b border-gray-100 shrink-0 shadow-sm z-10 bg-white">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                       {activeTeamData?.name?.substring(0,2).toUpperCase() || 'NA'}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{activeTeamData?.name?.split('—')[0]?.trim() || 'Select Team'}</h2>
                      <div className="flex items-center gap-4 text-xs font-semibold text-gray-500 mt-1">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Active Policy</span>
                        <span>{assignments[selectedTeam]?.size || 0} selected of {tables.length}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center bg-gray-100 rounded-lg p-1">
                    <button className="px-3 py-1.5 bg-white shadow-sm rounded-md text-sm font-bold text-gray-900">Data Tables</button>
                    <button className="px-3 py-1.5 text-gray-500 hover:text-gray-900 rounded-md text-sm font-bold transition-colors">Users</button>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="relative flex-1">
                    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} type="text" placeholder="Search tables across all schemas..." className="w-full pl-9 pr-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"/>
                  </div>
                  <button className="px-3 py-2 bg-gray-50 border border-gray-200 text-gray-700 font-bold text-sm rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px]">filter_list</span> Schema
                  </button>
                </div>
              </div>

              {/* Tables List */}
              <div className="flex-1 overflow-y-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
                    <tr>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-200 w-16">Active</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-200">Table Signature</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-200">Access Status</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-200 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredTables.map((table) => {
                      const isChecked = assignments[selectedTeam]?.has(table.table_name) || false
                      return (
                        <tr key={table.table_name} className={`${isChecked ? 'bg-indigo-50/30' : 'hover:bg-primary/5'} transition-colors`} onClick={() => toggleTable(table.table_name)}>
                          <td className="px-6 py-4">
                            <label className="relative flex items-center cursor-pointer ml-2">
                              <input type="checkbox" className="sr-only peer" checked={isChecked} readOnly />
                              <div className={`w-5 h-5 border-2 rounded transition duration-200 ease-in-out flex items-center justify-center ${isChecked ? 'border-primary bg-primary' : 'border-gray-300'}`}>
                                <span className={`material-symbols-outlined text-white text-[14px] transition-opacity ${isChecked ? 'opacity-100' : 'opacity-0'}`}>check</span>
                              </div>
                            </label>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <span className={`material-symbols-outlined p-1.5 rounded text-[16px] ${isChecked ? 'text-indigo-500 bg-indigo-100' : 'text-gray-400 bg-gray-100'}`}>table</span>
                              <div>
                                <div className="flex items-center gap-1.5 font-mono text-sm">
                                  <span className={isChecked ? "text-indigo-900 font-bold" : "text-gray-700 font-bold"}>{table.table_name}</span>
                                </div>
                                <div className={`text-[10px] tracking-wider uppercase font-semibold mt-1 ${isChecked ? 'text-indigo-600' : 'text-gray-400'}`}>
                                  {table.column_count} columns
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex gap-1 flex-wrap">
                               {table.team_assignments?.length > 0 ? (
                                  table.team_assignments.map(a => (
                                      <span key={a.team_id} className="text-xs bg-gray-100 text-gray-500 font-bold px-2 py-1 rounded">
                                        {a.team_name.split('')[0]}
                                      </span>
                                  ))
                               ) : (
                                 <span className="text-xs text-gray-400 italic">No access</span>
                               )}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-right">
                             <button className="text-gray-400 hover:text-primary transition-colors p-1 bg-gray-50 hover:bg-indigo-50 rounded">
                               <span className="material-symbols-outlined text-[18px]">edit</span>
                             </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'users' && (
          <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 p-8 overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Cross-Team Permissions</h2>
            <p className="text-sm text-gray-500 mb-8 max-w-2xl">Enterprise Analysts can query across multiple teams simultaneously via the Agentic Router. Revoking access dynamically removes vectors from their local context.</p>

            <div className="grid grid-cols-2 gap-4">
              {users.map(user => (
                <div key={user.id} className="border border-gray-200 p-5 rounded-xl shadow-sm flex flex-col gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-bold text-gray-900 text-lg">{user.name}</div>
                      <span className={`text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded ${user.role === 'ENTERPRISE_ANALYST' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'}`}>
                        {user.role}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 font-mono">{user.email}</div>
                  </div>
                  <div className="border-t border-gray-100 pt-3 flex flex-wrap gap-2">
                    {teams.map(team => {
                      const hasAccess = user.accessible_teams.some(a => a.team_id === team.id)
                      return (
                        <button
                          key={team.id}
                          onClick={() => updateUserAccess(user.id, hasAccess ? user.accessible_teams.map(a => a.team_id).filter(id => id !== team.id) : [...user.accessible_teams.map(a => a.team_id), team.id])}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                            hasAccess 
                              ? 'bg-primary text-white border-primary shadow-sm' 
                              : 'bg-white text-gray-500 border-gray-200 hover:border-primary hover:text-primary'
                          }`}
                        >
                          {hasAccess ? '✓ ' : ''} {team.name.split('—')[0]?.trim()}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
