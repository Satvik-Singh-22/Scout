'use client'

import { useState, useEffect, useMemo } from 'react'
import { adminGetTables, adminGetTeams, adminGetUsers, adminAssignTables, adminRevokeTable, adminUpdateUserAccess } from '@/lib/api-client'
import type { AdminTable, AdminTeam, AdminUser } from '@/lib/api-client'

const PAGE_SIZE = 8

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'tables' | 'users'>('tables')
  const [tables, setTables] = useState<AdminTable[]>([])
  const [teams, setTeams] = useState<AdminTeam[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState<'success' | 'error'>('success')
  const [searchQuery, setSearchQuery] = useState('')
  const [teamSearchQuery, setTeamSearchQuery] = useState('')
  const [page, setPage] = useState(1)

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
        return {
          table_name: name,
          semantic_definition: `Data from ${name} table.`,
          columns_metadata: []
        }
      })

      if (tableAssignments.length > 0) {
        await adminAssignTables({ team_id: selectedTeam, table_assignments: tableAssignments })
      }

      setMessage('Rules published successfully — AI analysis complete.')
      setMessageType('success')
      const updated = await adminGetTables()
      setTables(updated)
    } catch {
      setMessage('Failed to publish rules. Please retry.')
      setMessageType('error')
    }
    setSaving(false)
    setTimeout(() => setMessage(''), 5000)
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
  const filteredTables = useMemo(() =>
    tables.filter(t => t.table_name.toLowerCase().includes(searchQuery.toLowerCase())),
    [tables, searchQuery]
  )

  const filteredTeams = useMemo(() =>
    teams.filter(t => t.name.toLowerCase().includes(teamSearchQuery.toLowerCase())),
    [teams, teamSearchQuery]
  )

  const totalPages = Math.ceil(filteredTables.length / PAGE_SIZE)
  const paginatedTables = filteredTables.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const selectedCount = assignments[selectedTeam]?.size || 0

  // Select All logic — operates on ALL filtered tables (not just current page)
  const allFilteredSelected = filteredTables.length > 0 && filteredTables.every(t => assignments[selectedTeam]?.has(t.table_name))
  const someFilteredSelected = filteredTables.some(t => assignments[selectedTeam]?.has(t.table_name))

  const toggleSelectAll = () => {
    setAssignments(prev => {
      const teamSet = new Set(prev[selectedTeam] || [])
      if (allFilteredSelected) {
        filteredTables.forEach(t => teamSet.delete(t.table_name))
      } else {
        filteredTables.forEach(t => teamSet.add(t.table_name))
      }
      return { ...prev, [selectedTeam]: teamSet }
    })
  }

  // Reset page when search or team changes
  useEffect(() => { setPage(1) }, [searchQuery, selectedTeam])

  // Generate a schema-like path from table name
  const getSchemaPath = (name: string) => {
    const parts = name.replace('mock_', '').split('_')
    if (parts.length >= 2) return `public.${parts[0]}.${parts.slice(1).join('_')}`
    return `public.${parts[0]}`
  }

  // Determine table type
  const getTableType = (name: string): 'TABLE' | 'VIEW' => {
    if (name.includes('log') || name.includes('audit') || name.includes('trail')) return 'VIEW'
    return 'TABLE'
  }

  if (loading) return (
    <div className="flex-1 w-full bg-[#f8f7ff] flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-2xl bg-[#635bff]/10 flex items-center justify-center">
          <div className="w-6 h-6 border-[3px] border-[#635bff] border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
      <div className="text-center">
        <div className="text-sm font-bold text-[#635bff] tracking-wide">INITIALIZING GOVERNANCE</div>
        <div className="text-xs text-gray-400 mt-1">Loading secure workspace data...</div>
      </div>
    </div>
  )

  return (
    <div className="flex-1 w-full bg-[#f8f7ff] flex flex-col h-[calc(100vh-64px)] max-h-[calc(100vh-64px)] overflow-hidden">

      {/* ============ HEADER ============ */}
      <div className="px-8 pt-7 pb-0 shrink-0 z-10">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-[28px] font-extrabold tracking-tight text-gray-900">Governance Console</h1>
            <p className="text-gray-500 text-sm mt-1.5 font-medium">Cross-team table assignment and permission orchestration.</p>
          </div>
          <div className="flex items-center gap-3">
            {message && (
              <div className={`flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-full animate-fade-in ${messageType === 'success' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-red-50 text-red-600 border border-red-200'}`}>
                <span className="material-symbols-outlined text-[16px]">{messageType === 'success' ? 'check_circle' : 'error'}</span>
                {message}
              </div>
            )}
            <button
              onClick={saveAssignments}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-[#635bff] text-white font-bold text-sm rounded-xl hover:bg-[#5248f0] hover:shadow-lg hover:shadow-[#635bff]/25 transition-all disabled:opacity-60 disabled:hover:shadow-none shadow-md shadow-[#635bff]/20"
            >
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Publishing & AI Analysis...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">cloud_upload</span>
                  Save Publish Rules
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 mb-0">
          <div className="px-5 py-2.5 text-sm font-semibold rounded-t-xl transition-all bg-[#635bff] text-white shadow-sm">
            Table Allocations
          </div>
        </div>
      </div>

      {/* ============ MAIN CONTENT ============ */}
      <div className="flex-1 flex overflow-hidden px-8 pb-4 min-h-0">

        {activeTab === 'tables' && (
          <div className="flex gap-5 flex-1 min-h-0 w-full">

            {/* ── LEFT PANEL: AVAILABLE TEAMS ── */}
            <div className="w-72 flex flex-col shrink-0 bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-hidden min-h-0">
              {/* Panel Header */}
              <div className="p-4 border-b border-gray-100 shrink-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px] text-[#635bff]">groups</span>
                    <h2 className="text-[11px] uppercase tracking-[0.15em] font-extrabold text-gray-900">Available Teams</h2>
                  </div>
                  <button
                    onClick={() => setTeamSearchQuery(teamSearchQuery ? '' : ' ')}
                    className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-[#635bff] hover:bg-[#635bff]/5 rounded-lg transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">search</span>
                  </button>
                </div>
                {teamSearchQuery !== '' && (
                  <input
                    value={teamSearchQuery.trim()}
                    onChange={(e) => setTeamSearchQuery(e.target.value)}
                    placeholder="Filter teams..."
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs focus:border-[#635bff] focus:ring-1 focus:ring-[#635bff]/20 outline-none transition-all"
                    autoFocus
                  />
                )}
              </div>

              {/* Team List */}
              <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
                {filteredTeams.map((team) => {
                  const isSelected = selectedTeam === team.id
                  const assignedCount = assignments[team.id]?.size || 0
                  return (
                    <div
                      key={team.id}
                      onClick={() => setSelectedTeam(team.id)}
                      className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 group ${isSelected ? 'bg-[#f0eeff] border-2 border-[#635bff]/30 shadow-sm' : 'border-2 border-transparent hover:bg-gray-50'}`}
                    >
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${isSelected ? 'bg-[#635bff] text-white shadow-sm shadow-[#635bff]/25' : 'bg-gray-100 text-gray-500'}`}>
                        {team.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-bold truncate ${isSelected ? 'text-[#635bff]' : 'text-gray-800'}`}>
                          {team.name.split('—')[0]?.trim()}
                        </div>
                        <div className={`text-[10px] font-bold uppercase tracking-wider mt-0.5 whitespace-nowrap ${isSelected ? 'text-[#635bff]/60' : 'text-gray-400'}`}>
                          {assignedCount} Tables Assigned
                        </div>
                      </div>
                      {isSelected && (
                        <span className="material-symbols-outlined text-[#635bff] text-[20px] shrink-0">chevron_right</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* ── RIGHT PANEL: TABLE ALLOCATION ── */}
            <div className="flex-1 bg-white rounded-2xl border border-gray-200/80 shadow-sm flex flex-col overflow-hidden min-h-0">

              {/* Team Header */}
              <div className="p-5 border-b border-gray-100 shrink-0">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-[#635bff] text-white flex items-center justify-center font-black text-lg shadow-sm shadow-[#635bff]/20">
                      {activeTeamData?.name?.substring(0, 2).toUpperCase() || 'NA'}
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h2 className="text-xl font-bold text-gray-900 leading-none">{activeTeamData?.name?.split('—')[0]?.trim() || 'Select Team'}</h2>
                        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 rounded-full border border-emerald-200/60 self-center">
                          <div className="relative flex items-center justify-center w-2 h-2">
                            <span className="absolute w-full h-full bg-emerald-500 rounded-full animate-ping opacity-75"></span>
                            <span className="relative w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                          </div>
                          <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider leading-none">Active Policy</span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1.5 font-medium">
                        {selectedCount} selected of {filteredTables.length} total assigned tables
                      </p>
                    </div>
                  </div>
                </div>

                {/* Search Bar */}
                <div className="flex items-center gap-3">
                  <div className="relative flex-1">
                    <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      type="text"
                      placeholder="Search tables across all schemas..."
                      className="w-full pl-11 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:border-[#635bff] focus:ring-2 focus:ring-[#635bff]/10 focus:bg-white outline-none transition-all placeholder:text-gray-400 font-medium"
                    />
                  </div>
                  <button
                    onClick={toggleSelectAll}
                    className={`px-4 py-2.5 font-semibold text-sm rounded-xl transition-all flex items-center gap-2 border whitespace-nowrap ${
                      allFilteredSelected
                        ? 'bg-amber-50 border-amber-300 text-amber-700 hover:bg-amber-100'
                        : 'bg-[#f0eeff] border-[#635bff]/20 text-[#635bff] hover:bg-[#e8e5ff]'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {allFilteredSelected ? 'deselect' : 'select_all'}
                    </span>
                    {allFilteredSelected ? 'Deselect All' : 'Select All'}
                    <span className="text-[10px] opacity-60 font-bold">({filteredTables.length})</span>
                  </button>
                  <button className="px-4 py-2.5 bg-gray-50 border border-gray-200 text-gray-600 font-semibold text-sm rounded-xl hover:bg-gray-100 transition-all flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">tune</span>
                    Schema
                  </button>
                </div>
              </div>

              {/* Table Grid */}
              <div className="flex-1 overflow-y-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-gray-50/80 sticky top-0 z-10">
                    <tr>
                      <th className="px-5 py-3 border-b border-gray-100 w-12">
                        <label className="relative flex items-center cursor-pointer">
                          <input type="checkbox" className="sr-only peer" checked={allFilteredSelected} onChange={toggleSelectAll} />
                          <div
                            className={`w-[18px] h-[18px] border-2 rounded-md transition-all duration-200 flex items-center justify-center ${
                              allFilteredSelected
                                ? 'border-[#635bff] bg-[#635bff]'
                                : someFilteredSelected
                                  ? 'border-[#635bff] bg-[#635bff]/50'
                                  : 'border-gray-300 hover:border-[#635bff]/40'
                            }`}
                            title={allFilteredSelected ? 'Deselect all tables' : 'Select all tables'}
                          >
                            <span className={`material-symbols-outlined text-white text-[13px] transition-opacity ${allFilteredSelected || someFilteredSelected ? 'opacity-100' : 'opacity-0'}`}>
                              {allFilteredSelected ? 'check' : 'remove'}
                            </span>
                          </div>
                        </label>
                      </th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-100 w-20">Type</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-100">Table Name</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-100">Schema/Path</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-100 w-28 text-right">Last Sync</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {paginatedTables.map((table) => {
                      const isChecked = assignments[selectedTeam]?.has(table.table_name) || false
                      const tableType = getTableType(table.table_name)
                      const schemaPath = getSchemaPath(table.table_name)
                      return (
                        <tr
                          key={table.table_name}
                          className={`${isChecked ? 'bg-[#f8f7ff]' : 'hover:bg-gray-50/60'} transition-all duration-150 cursor-pointer group`}
                          onClick={() => toggleTable(table.table_name)}
                        >
                          {/* Checkbox */}
                          <td className="px-5 py-4 align-middle">
                            <label className="relative flex items-center cursor-pointer">
                              <input type="checkbox" className="sr-only peer" checked={isChecked} readOnly />
                              <div className={`w-[18px] h-[18px] border-2 rounded-md transition-all duration-200 flex items-center justify-center ${isChecked ? 'border-[#635bff] bg-[#635bff]' : 'border-gray-300 group-hover:border-[#635bff]/40'}`}>
                                <span className={`material-symbols-outlined text-white text-[13px] transition-opacity ${isChecked ? 'opacity-100' : 'opacity-0'}`}>check</span>
                              </div>
                            </label>
                          </td>
                          {/* Type Badge */}
                          <td className="px-4 py-4">
                            <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${tableType === 'TABLE' ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'bg-amber-50 text-amber-600 border border-amber-100'}`}>
                              {tableType}
                            </span>
                          </td>
                          {/* Table Name */}
                          <td className="px-4 py-4">
                            <div>
                              <span className={`text-sm ${isChecked ? 'text-[#635bff] font-bold' : 'text-gray-800 font-semibold'}`}>
                                {table.table_name}
                              </span>
                              <div className="text-[10px] text-gray-400 font-medium mt-0.5">
                                {table.column_count} Columns
                              </div>
                            </div>
                          </td>
                          {/* Schema/Path */}
                          <td className="px-4 py-4">
                            <span className="inline-flex items-center px-2.5 py-1 bg-gray-50 text-gray-500 rounded-lg text-[11px] font-mono border border-gray-100">
                              {schemaPath}
                            </span>
                          </td>
                          {/* Last Sync */}
                          <td className="px-4 py-4 text-right align-middle">
                            <div className="inline-flex items-center gap-1.5">
                              <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${isChecked ? 'bg-emerald-400' : 'bg-gray-300'}`}></div>
                              <span className="text-[11px] text-gray-400 font-medium leading-none">
                                {isChecked ? 'Just now' : 'Inactive'}
                              </span>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                    {paginatedTables.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-16 text-center">
                          <span className="material-symbols-outlined text-4xl text-gray-300 mb-2 block">search_off</span>
                          <div className="text-sm text-gray-400 font-medium">No tables match your search criteria.</div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination Footer */}
              <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between shrink-0 bg-gray-50/50">
                <span className="text-[11px] text-gray-400 font-bold uppercase tracking-wider">
                  Showing {paginatedTables.length} of {filteredTables.length} allocated tables
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-1.5 text-xs font-semibold rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  >
                    Previous
                  </button>
                  <span className="text-xs text-gray-400 font-medium px-2">{page} / {totalPages || 1}</span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="px-4 py-1.5 text-xs font-semibold rounded-lg border border-[#635bff]/30 bg-[#635bff]/5 text-[#635bff] hover:bg-[#635bff]/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============ USERS TAB ============ */}
        {activeTab === 'users' && (
          <div className="flex-1 bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-y-auto">
            <div className="p-8">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-[#635bff]/10 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[#635bff] text-[22px]">group</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Cross-Team Routing Access</h2>
                  <p className="text-xs text-gray-500 font-medium">Manage analyst access to multiple tenant workspaces.</p>
                </div>
              </div>
            </div>

            <div className="px-8 pb-8 grid grid-cols-1 xl:grid-cols-2 gap-4">
              {users.map(user => (
                <div key={user.id} className="border border-gray-100 p-5 rounded-2xl hover:shadow-md transition-all bg-gradient-to-br from-white to-gray-50/50 group">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#635bff]/10 text-[#635bff] flex items-center justify-center font-bold text-sm">
                        {user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900 text-sm">{user.name}</div>
                        <div className="text-xs text-gray-400 font-medium">{user.email}</div>
                      </div>
                    </div>
                    <span className={`text-[9px] uppercase tracking-[0.15em] font-extrabold px-3 py-1.5 rounded-lg ${user.role === 'ENTERPRISE_ANALYST' ? 'bg-[#635bff] text-white' : user.role === 'PLATFORM_ADMIN' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-gray-100 text-gray-500 border border-gray-200'}`}>
                      {user.role.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="border-t border-gray-100 pt-3 flex flex-wrap gap-1.5">
                    {teams.map(team => {
                      const hasAccess = user.accessible_teams.some(a => a.team_id === team.id)
                      return (
                        <button
                          key={team.id}
                          onClick={() => updateUserAccess(user.id, hasAccess ? user.accessible_teams.map(a => a.team_id).filter(id => id !== team.id) : [...user.accessible_teams.map(a => a.team_id), team.id])}
                          className={`px-3 py-1.5 rounded-lg text-[11px] font-bold border transition-all flex items-center gap-1 ${hasAccess
                            ? 'bg-[#f0eeff] text-[#635bff] border-[#635bff]/20'
                            : 'bg-white text-gray-400 border-gray-100 hover:border-[#635bff]/20 hover:text-[#635bff]'
                            }`}
                        >
                          {hasAccess && <span className="material-symbols-outlined text-[12px]">check</span>}
                          {team.name.split('—')[0]?.trim()}
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

      {/* ============ BOTTOM STATUS BAR ============ */}
    </div>
  )
}
