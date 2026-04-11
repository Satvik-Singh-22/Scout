'use client'
import { useEffect, useState } from 'react'
import { getMe, updateMe, User } from '@/lib/api-client'
import { Settings } from 'lucide-react'

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getMe().then(u => {
      setUser(u)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setMessage('')
    try {
      const updated = await updateMe({ persona: user.persona, name: user.name })
      setUser(updated)
      setMessage('Settings updated successfully.')
    } catch {
      setMessage('Failed to update settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex items-center justify-center p-12 text-gray-400">Loading settings...</div>
  if (!user) return <div className="flex items-center justify-center p-12 text-gray-400">Not authenticated.</div>

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-8">
        <Settings className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500">Manage your persona and preferences</p>
        </div>
      </div>
      
      <div className="bg-white border rounded-xl shadow-sm p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input 
              type="text" 
              value={user.name} 
              onChange={e => setUser({...user, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email (Read Only)</label>
            <input 
              type="text" 
              value={user.email} 
              disabled
              className="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500 max-w-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role (Read Only)</label>
            <input 
              type="text" 
              value={user.role} 
              disabled
              className="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500 max-w-sm"
            />
          </div>

          {/* Team info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Team</label>
            {user.accessible_teams && user.accessible_teams.length > 0 ? (
              <div className="space-y-2">
                {user.accessible_teams.map(team => (
                  <div
                    key={team.team_id}
                    className={`inline-flex items-center gap-2 mr-2 px-3 py-2 rounded-lg border text-sm ${
                      team.team_id === user.team_id
                        ? 'bg-indigo-50 border-indigo-200 text-indigo-700 font-medium'
                        : 'bg-gray-50 border-gray-200 text-gray-600'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]">groups</span>
                    {team.team_name}
                    {team.team_id === user.team_id && (
                      <span className="text-[10px] font-bold bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded uppercase tracking-wide">Primary</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No team assigned</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Persona</label>
            <div className="grid grid-cols-2 gap-4">
              <label className={`border rounded-lg p-4 cursor-pointer transition-colors ${user.persona === 'MANAGER' ? 'border-indigo-600 bg-indigo-50' : 'hover:bg-gray-50'}`}>
                <div className="flex items-center gap-3 mb-1">
                  <input type="radio" checked={user.persona === 'MANAGER'} onChange={() => setUser({...user, persona: 'MANAGER'})} className="accent-indigo-600" />
                  <span className="font-medium text-gray-900">Manager</span>
                </div>
                <p className="text-xs text-gray-500 ml-6">Simplified charts and executive summaries.</p>
              </label>

              <label className={`border rounded-lg p-4 cursor-pointer transition-colors ${user.persona === 'DEVELOPER' ? 'border-indigo-600 bg-indigo-50' : 'hover:bg-gray-50'}`}>
                <div className="flex items-center gap-3 mb-1">
                  <input type="radio" checked={user.persona === 'DEVELOPER'} onChange={() => setUser({...user, persona: 'DEVELOPER'})} className="accent-indigo-600" />
                  <span className="font-medium text-gray-900">Developer</span>
                </div>
                <p className="text-xs text-gray-500 ml-6">Raw data tables, full SQL visibility, and strict schemas.</p>
              </label>
            </div>
          </div>

          <div className="pt-4 flex items-center gap-4 border-t">
            <button type="submit" disabled={saving} className="bg-indigo-600 text-white font-medium px-6 py-2 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
            {message && <span className="text-sm text-green-600 font-medium">{message}</span>}
          </div>
        </form>
      </div>
    </div>
  )
}
