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
import { useEffect, useState } from 'react'
import { getMe, updateMe, User } from '@/lib/api-client'
import { User as UserIcon, Users, Check } from 'lucide-react'

export default function ProfilePage() {
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
      const updated = await updateMe({
        name: user.name,
        team_id: user.team_id || undefined
      })
      setUser(prev => prev ? { ...prev, ...updated } : updated)
      setMessage('Profile updated successfully.')
    } catch {
      setMessage('Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex items-center justify-center p-12 text-gray-400">Loading profile...</div>
  if (!user) return <div className="flex items-center justify-center p-12 text-gray-400">Not authenticated.</div>

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-8">
        <UserIcon className="text-indigo-600" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
          <p className="text-sm text-gray-500">Manage your account details</p>
        </div>
      </div>

      <div className="bg-white border rounded-xl shadow-sm p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              value={user.name}
              onChange={e => setUser({ ...user, name: e.target.value })}
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
              value={user.role ? user.role.replace('_', ' ') : ''}
              disabled
              className="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500 max-w-sm capitalize"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Teams
            </label>
            <p className="text-xs text-gray-500 mb-3">
              Click a team to make it your active workspace.
            </p>

            {user.accessible_teams && user.accessible_teams.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {user.accessible_teams.map((team) => {
                  const isPrimary = team.team_id === user.team_id

                  return (
                    <div
                      key={team.team_id}
                      onClick={() => !saving && setUser({ ...user, team_id: team.team_id })}
                      className={`flex items-center justify-between border rounded-xl px-4 py-3 transition-all duration-150 cursor-pointer ${isPrimary
                        ? "border-indigo-200 bg-indigo-50 ring-1 ring-indigo-200"
                        : "border-gray-200 bg-white hover:bg-gray-50"
                        }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-lg ${isPrimary ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-500"
                            }`}
                        >
                          <Users size={18} />
                        </div>

                        <div className="min-w-0">
                          <p
                            className={`text-sm font-medium truncate ${isPrimary ? "text-indigo-700" : "text-gray-800"
                              }`}
                          >
                            {team.team_name}
                          </p>

                          <p className="text-xs text-gray-400 truncate" title={team.team_id}>
                            Team ID: {team.team_id}
                          </p>
                        </div>
                      </div>

                      {isPrimary && (
                        <span className="flex-shrink-0 flex items-center gap-1 text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-1 rounded-md border border-indigo-200 uppercase tracking-wider">
                          <Check size={10} strokeWidth={3} />
                          Primary
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="border border-dashed border-gray-300 rounded-lg p-4 text-sm text-gray-400 italic">
                No team assigned
              </div>
            )}
          </div>

          <div className="pt-4 flex items-center gap-4 border-t">
            <button type="submit" disabled={saving} className="bg-indigo-600 text-white font-medium px-6 py-2 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
            {message && <span className="text-sm text-green-600 font-medium">{message}</span>}
          </div>
        </form>
      </div>
    </div>
  )
}
