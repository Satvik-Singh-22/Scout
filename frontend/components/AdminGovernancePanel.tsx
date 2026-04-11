'use client'
import { useState, useEffect } from 'react'
import { adminGetTables, adminGetTeams, adminGetUsers, adminAssignTables, adminRevokeTable, adminUpdateUserAccess } from '@/lib/api-client'
import type { AdminTable, AdminTeam, AdminUser } from '@/lib/api-client'

export default function AdminGovernancePanel() {
  const [activeTab, setActiveTab] = useState<'tables' | 'users'>('tables')
  const [tables, setTables] = useState<AdminTable[]>([])
  const [teams, setTeams] = useState<AdminTeam[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const [assignments, setAssignments] = useState<Record<string, Set<string>>>({})

  useEffect(() => {
    Promise.all([adminGetTables(), adminGetTeams(), adminGetUsers()])
      .then(([t, teams, users]) => {
        setTables(t)
        setTeams(teams)
        setUsers(users)
        if (teams.length > 0) setSelectedTeam(teams[0].id)

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

      setMessage('Configuration synchronized successfully.')
      const updated = await adminGetTables()
      setTables(updated)
    } catch {
      setMessage('Synchronization failed.')
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-gray-400">
        Authenticating Platform Admin access...
      </div>
    )
  }

  const activeTeamData = teams.find(t => t.id === selectedTeam)
  const filteredTables = tables.filter(t => t.table_name.toLowerCase().includes(searchQuery.toLowerCase()))

  const allFilteredSelected = filteredTables.length > 0 && filteredTables.every(t => assignments[selectedTeam]?.has(t.table_name))
  const someFilteredSelected = filteredTables.some(t => assignments[selectedTeam]?.has(t.table_name))

  const toggleSelectAll = () => {
    setAssignments(prev => {
      const teamSet = new Set(prev[selectedTeam] || [])
      if (allFilteredSelected) {
        // Deselect all filtered tables
        filteredTables.forEach(t => teamSet.delete(t.table_name))
      } else {
        // Select all filtered tables
        filteredTables.forEach(t => teamSet.add(t.table_name))
      }
      return { ...prev, [selectedTeam]: teamSet }
    })
  }

  return (
    <div className="max-w-7xl mx-auto h-screen overflow-hidden flex flex-col">

      {/* Tab Navigation */}
      <div className="flex gap-4 border-b border-gray-200 shrink-0">
        <button
          className={`pb-4 px-2 text-sm font-bold transition-all relative ${activeTab === 'tables' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'}`}
          onClick={() => setActiveTab('tables')}
        >
          Table Assignment
          {activeTab === 'tables' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600" />}
        </button>
        <button
          className={`pb-4 px-2 text-sm font-bold transition-all relative ${activeTab === 'users' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'}`}
          onClick={() => setActiveTab('users')}
        >
          Cross-Team Access
          {activeTab === 'users' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600" />}
        </button>
      </div>

      {/* Tables Tab Config */}
      {activeTab === 'tables' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 flex-1 overflow-hidden">
          {/* Sidebar - Teams */}
          <div className="col-span-1 bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-100 bg-gray-50/50">
              <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Tenant Workspaces</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {teams.map(team => (
                <button
                  key={team.id}
                  onClick={() => setSelectedTeam(team.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all text-left ${selectedTeam === team.id
                    ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                    : 'border-transparent hover:bg-gray-50'
                    }`}
                >
                  <div>
                    <div className={`text-sm font-bold ${selectedTeam === team.id ? 'text-indigo-900' : 'text-gray-900'}`}>
                      {team.name}
                    </div>
                    <div className={`text-[10px] mt-0.5 font-semibold uppercase tracking-wider ${selectedTeam === team.id ? 'text-indigo-600' : 'text-gray-500'
                      }`}>
                      {team.table_count || 0} Tables Linked
                    </div>
                  </div>
                  {selectedTeam === team.id && (
                    <span className="material-symbols-outlined text-indigo-600">chevron_right</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Main Area - Tables */}
          <div className="col-span-3 bg-white border border-gray-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-200 shrink-0">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{activeTeamData?.name || 'Select Team'} Data Configuration</h2>
                  <p className="text-sm text-gray-500 mt-1">Assign data warehouse tables to the {activeTeamData?.name} semantic pool.</p>
                </div>
                <div className="flex items-center gap-3">
                  {message && <span className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">{message}</span>}
                  <button
                    onClick={toggleSelectAll}
                    className={`flex items-center gap-2 px-4 py-2.5 font-bold text-sm rounded-lg border-2 transition-all ${allFilteredSelected
                      ? 'border-amber-400 bg-amber-50 text-amber-700 hover:bg-amber-100'
                      : 'border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                      }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {allFilteredSelected ? 'deselect' : 'select_all'}
                    </span>
                    {allFilteredSelected ? 'Deselect All' : 'Select All'}
                    <span className="ml-1 text-xs opacity-70">({filteredTables.length})</span>
                  </button>
                  <button
                    onClick={saveAssignments}
                    disabled={saving}
                    className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white font-bold text-sm rounded-lg hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-[18px]">save</span>
                    {saving ? 'Syncing...' : 'Save & Publish'}
                  </button>
                </div>
              </div>

              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">search</span>
                <input
                  type="text"
                  placeholder="Filter tables by name or identifier..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {filteredTables.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No tables found matching criteria.</div>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50/80 sticky top-0 backdrop-blur-sm shadow-sm z-10">
                    <tr>
                      <th className="px-6 py-3 w-16 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={allFilteredSelected}
                          ref={(el) => { if (el) el.indeterminate = someFilteredSelected && !allFilteredSelected }}
                          onChange={toggleSelectAll}
                          className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-600 cursor-pointer"
                          title={allFilteredSelected ? 'Deselect all visible tables' : 'Select all visible tables'}
                        />
                      </th>
                      <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Table Identifier</th>
                      <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Schema Shape</th>
                      <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Global Tenants</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredTables.map(table => {
                      const isChecked = assignments[selectedTeam]?.has(table.table_name) || false
                      return (
                        <tr
                          key={table.table_name}
                          onClick={() => toggleTable(table.table_name)}
                          className={`cursor-pointer transition-colors ${isChecked ? 'bg-indigo-50/30 hover:bg-indigo-50/60' : 'hover:bg-gray-50'}`}
                        >
                          <td className="px-6 py-4 text-center">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              readOnly
                              className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-600 cursor-pointer pointer-events-none"
                            />
                          </td>
                          <td className="px-6 py-4 font-mono font-medium text-gray-900">{table.table_name}</td>
                          <td className="px-6 py-4 text-gray-500">{table.column_count} columns encoded</td>
                          <td className="px-6 py-4">
                            <div className="flex gap-1.5 flex-wrap">
                              {table.team_assignments.filter(a => a.is_active).map(a => (
                                <span key={a.team_id} className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${a.team_name === activeTeamData?.name ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'
                                  }`}>
                                  {a.team_name}
                                </span>
                              ))}
                              {table.team_assignments.filter(a => a.is_active).length === 0 && (
                                <span className="text-xs text-gray-400 italic">Orphaned data</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Users Tab Config */}
      {activeTab === 'users' && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 flex-1 overflow-y-auto">
          <div className="max-w-3xl">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Cross-Domain Analytics Privileges</h2>
            <p className="text-sm text-gray-500 mb-8 leading-relaxed">
              Enterprise Analysts possess the capability to run multi-domain queries via the conversational router.
              Toggle the workspaces below to actively weave standard semantic layers into their local vector context.
            </p>

            <div className="space-y-4">
              {users.filter(u => u.role === 'ENTERPRISE_ANALYST' || u.role === 'ANALYST').map(user => (
                <div key={user.id} className="border border-gray-200 p-5 rounded-xl bg-gray-50/30 flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-bold text-gray-900 text-lg flex items-center gap-2">
                        {user.name}
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${user.role === 'ENTERPRISE_ANALYST' ? 'bg-indigo-100 text-indigo-700' : 'bg-white border border-gray-300 text-gray-600'
                          }`}>
                          {user.role.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500 font-mono mt-1">{user.email}</div>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-4 flex flex-wrap gap-2">
                    {teams.map(team => {
                      const hasAccess = user.accessible_teams.some(a => a.team_id === team.id)
                      const onClick = () => {
                        const newIds = hasAccess
                          ? user.accessible_teams.map(a => a.team_id).filter(id => id !== team.id)
                          : [...user.accessible_teams.map(a => a.team_id), team.id]
                        updateUserAccess(user.id, newIds)
                      }

                      return (
                        <button
                          key={team.id}
                          onClick={onClick}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all flex items-center gap-1.5 ${hasAccess
                            ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm hover:bg-indigo-700'
                            : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400 hover:text-indigo-600'
                            }`}
                        >
                          <span className="material-symbols-outlined text-[14px]">
                            {hasAccess ? 'check_circle' : 'add_circle'}
                          </span>
                          {team.name}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}

              {users.filter(u => u.role === 'ENTERPRISE_ANALYST' || u.role === 'ANALYST').length === 0 && (
                <div className="p-8 text-center text-gray-500 border-2 border-dashed border-gray-200 rounded-xl">
                  No eligible analysts found in the registry.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
