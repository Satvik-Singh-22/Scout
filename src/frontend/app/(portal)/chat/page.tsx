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

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { getChatrooms, createChatroom, renameChatroom, deleteChatroom } from '@/lib/api-client'
import type { Chatroom } from '@/lib/api-client'
import { AGENT_MODES, getAgentModeConfig } from '@/lib/agent-modes'
import type { AgentMode } from '@/lib/agent-modes'

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function ChatHubPage() {
  const router = useRouter()
  const [chatrooms, setChatrooms] = useState<Chatroom[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [showNewChatModal, setShowNewChatModal] = useState(false)

  // Inline rename state
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')
  const [renameLoading, setRenameLoading] = useState(false)
  const editInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    getChatrooms()
      .then(data => { setChatrooms(data); setLoading(false) })
      .catch(err => { setError(err.message || 'Failed to load sessions'); setLoading(false) })
  }, [])

  // Focus the input when editing starts
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus()
      editInputRef.current.select()
    }
  }, [editingId])

  // Close modal on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowNewChatModal(false)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const handleNewChat = async (mode: AgentMode) => {
    setCreating(true)
    setShowNewChatModal(false)
    setError('')
    try {
      const config = getAgentModeConfig(mode)
      const room = await createChatroom('New Conversation', mode)
      router.push(`/chat/${room.id}`)
    } catch (err: unknown) {
      setCreating(false)
      setError(err instanceof Error ? err.message : 'Failed to create chat session')
    }
  }

  const handleOpenRoom = (id: string) => {
    if (editingId === id) return // Don't navigate while editing
    router.push(`/chat/${id}`)
  }

  const startEditing = (e: React.MouseEvent, room: Chatroom) => {
    e.stopPropagation()
    setEditingId(room.id)
    setEditingName(room.name)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditingName('')
  }

  const saveRename = async () => {
    if (!editingId || !editingName.trim() || renameLoading) return
    const trimmedName = editingName.trim()
    // Find original name to check if changed
    const original = chatrooms.find(r => r.id === editingId)
    if (original && original.name === trimmedName) {
      cancelEditing()
      return
    }
    setRenameLoading(true)
    try {
      const updated = await renameChatroom(editingId, trimmedName)
      setChatrooms(prev => prev.map(r => r.id === updated.id ? { ...r, name: updated.name } : r))
      cancelEditing()
    } catch {
      setError('Failed to rename chat session')
    } finally {
      setRenameLoading(false)
    }
  }

  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      saveRename()
    } else if (e.key === 'Escape') {
      cancelEditing()
    }
  }

  const handleDeleteChat = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this chat session? This cannot be undone.')) return

    try {
      await deleteChatroom(id)
      setChatrooms(prev => prev.filter(r => r.id !== id))
    } catch {
      setError('Failed to delete chat session')
    }
  }

  return (
    <div className="p-8 max-w-7xl w-full mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Chat Sessions</h1>
          <p className="text-gray-500 text-sm mt-1">Ask natural language questions about your enterprise data.</p>
        </div>
        <button
          onClick={() => setShowNewChatModal(true)}
          disabled={creating}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          {creating ? 'Creating…' : 'New Chat'}
        </button>
      </div>

      {/* Agent Selection Modal */}
      {showNewChatModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowNewChatModal(false)}>
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">Choose Agent Type</h2>
              <p className="text-sm text-gray-500 mt-1">Select the intelligence pipeline for this conversation.</p>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Object.values(AGENT_MODES).map((mode) => (
                <button
                  key={mode.key}
                  onClick={() => handleNewChat(mode.key)}
                  className={`group relative flex flex-col items-center text-center p-6 rounded-xl border-2 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] ${mode.borderColor} hover:border-opacity-100 border-opacity-40 bg-white hover:${mode.bgColor}`}
                >
                  <div className={`w-14 h-14 rounded-2xl ${mode.bgColor} flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform`}>
                    {mode.icon}
                  </div>
                  <h3 className={`text-base font-bold text-gray-900 mb-1`}>{mode.label}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{mode.description}</p>
                  <div className={`mt-4 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${mode.badgeBg} ${mode.badgeText}`}>
                    {mode.shortLabel}
                  </div>
                </button>
              ))}
            </div>
            <div className="px-6 pb-5 flex justify-end">
              <button
                onClick={() => setShowNewChatModal(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-600 ml-2">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 h-48 animate-pulse">
              <div className="w-10 h-10 bg-gray-200 rounded-lg mb-4" />
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && chatrooms.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-indigo-400 text-3xl">chat_bubble_outline</span>
          </div>
          <h2 className="text-lg font-bold text-gray-700 mb-1">No sessions yet</h2>
          <p className="text-sm text-gray-400 mb-6">Start your first conversation with your data</p>
          <button
            onClick={() => setShowNewChatModal(true)}
            disabled={creating}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-all disabled:opacity-50"
          >
            {creating ? 'Creating…' : 'Start First Chat'}
          </button>
        </div>
      )}

      {/* Chatroom grid */}
      {!loading && chatrooms.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {chatrooms.map((room) => {
              const modeConfig = getAgentModeConfig(room.agent_mode)
              const isEditing = editingId === room.id
              return (
                <div
                  key={room.id}
                  onClick={() => handleOpenRoom(room.id)}
                  className={`group bg-white rounded-xl p-6 shadow-sm border transition-all duration-300 flex flex-col justify-between h-48 relative overflow-hidden ${isEditing ? 'border-indigo-300 shadow-md ring-2 ring-indigo-500/20' : 'border-gray-100/80 hover:shadow-xl hover:shadow-gray-200/60 cursor-pointer'}`}
                >
                  {/* Edit & Open icons */}
                  <div className="absolute top-0 right-0 p-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button
                      onClick={(e) => startEditing(e, room)}
                      className="p-1.5 rounded-lg hover:bg-indigo-50 text-gray-300 hover:text-indigo-500 transition-colors"
                      title="Rename chat"
                    >
                      <span className="material-symbols-outlined text-[16px]">edit</span>
                    </button>
                    <button
                      onClick={(e) => handleDeleteChat(e, room.id)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-500 transition-colors"
                      title="Delete chat"
                    >
                      <span className="material-symbols-outlined text-[16px]">delete</span>
                    </button>
                    <span className="material-symbols-outlined text-gray-300 text-[16px]">open_in_new</span>
                  </div>

                  <div>
                    <div className={`w-10 h-10 rounded-lg ${modeConfig.bgColor} ${modeConfig.accentColor} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform text-lg`}>
                      {modeConfig.icon}
                    </div>

                    {/* Inline rename input or title */}
                    {isEditing ? (
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <input
                          ref={editInputRef}
                          type="text"
                          value={editingName}
                          onChange={(e) => setEditingName(e.target.value)}
                          onKeyDown={handleEditKeyDown}
                          onBlur={saveRename}
                          maxLength={255}
                          disabled={renameLoading}
                          className="flex-1 text-sm font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 transition-all disabled:opacity-50"
                          placeholder="Chat name…"
                        />
                        <button
                          onClick={saveRename}
                          disabled={renameLoading || !editingName.trim()}
                          className="p-1 text-emerald-500 hover:text-emerald-600 disabled:opacity-40 transition-colors"
                          title="Save"
                        >
                          <span className="material-symbols-outlined text-[18px]">check</span>
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); cancelEditing() }}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          title="Cancel"
                        >
                          <span className="material-symbols-outlined text-[18px]">close</span>
                        </button>
                      </div>
                    ) : (
                      <h3 className="text-base font-bold text-gray-900 leading-tight truncate pr-12">{room.name}</h3>
                    )}

                    {room.last_message_preview && !isEditing && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-1">{room.last_message_preview}</p>
                    )}
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-gray-50">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${modeConfig.badgeBg} ${modeConfig.badgeText}`}>
                      {modeConfig.shortLabel}
                    </span>
                    <span className="text-xs text-gray-400">{timeAgo(room.created_at)}</span>
                  </div>
                </div>
              )
            })}

            {/* Start new thread card */}
            <div
              onClick={() => setShowNewChatModal(true)}
              className="group border-2 border-dashed border-gray-200 rounded-xl p-6 flex flex-col items-center justify-center h-48 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all cursor-pointer"
            >
              <div className="w-12 h-12 rounded-full bg-gray-50 group-hover:bg-indigo-100 text-gray-400 group-hover:text-indigo-500 flex items-center justify-center mb-3 transition-colors">
                <span className="material-symbols-outlined">add</span>
              </div>
              <span className="text-sm font-semibold text-gray-500 group-hover:text-indigo-600 transition-colors">
                {creating ? 'Creating…' : 'Start new session'}
              </span>
            </div>
          </div>

          {/* Stats row */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Total Sessions</div>
              <div className="text-2xl font-extrabold text-gray-900">{chatrooms.length}</div>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Today</div>
              <div className="text-2xl font-extrabold text-indigo-600">
                {chatrooms.filter(r => {
                  const diff = Date.now() - new Date(r.created_at).getTime()
                  return diff < 86400000
                }).length}
              </div>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">AI Engine</div>
              <div className="text-lg font-extrabold text-gray-900">LangGraph</div>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Status</div>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-sm font-bold text-emerald-600">Online</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
