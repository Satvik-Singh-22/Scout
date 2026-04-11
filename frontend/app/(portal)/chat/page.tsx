'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getChatrooms, createChatroom } from '@/lib/api-client'
import type { Chatroom } from '@/lib/api-client'

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

const ACCENT_COLORS = [
  { bg: 'bg-indigo-50', text: 'text-indigo-600', badge: 'bg-indigo-100 text-indigo-600', icon: '📊' },
  { bg: 'bg-emerald-50', text: 'text-emerald-600', badge: 'bg-emerald-100 text-emerald-600', icon: '🔍' },
  { bg: 'bg-orange-50', text: 'text-orange-600', badge: 'bg-orange-100 text-orange-600', icon: '📈' },
  { bg: 'bg-purple-50', text: 'text-purple-600', badge: 'bg-purple-100 text-purple-600', icon: '🧠' },
]

export default function ChatHubPage() {
  const router = useRouter()
  const [chatrooms, setChatrooms] = useState<Chatroom[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getChatrooms()
      .then(data => { setChatrooms(data); setLoading(false) })
      .catch(err => { setError(err.message || 'Failed to load sessions'); setLoading(false) })
  }, [])

  const handleNewChat = async () => {
    setCreating(true)
    setError('')
    try {
      const room = await createChatroom('New Conversation')
      router.push(`/chat/${room.id}`)
    } catch (err: unknown) {
      setCreating(false)
      setError(err instanceof Error ? err.message : 'Failed to create chat session')
    }
  }

  const handleOpenRoom = (id: string) => {
    router.push(`/chat/${id}`)
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
          onClick={handleNewChat}
          disabled={creating}
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          {creating ? 'Creating…' : 'New Chat'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
          {error}
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
            onClick={handleNewChat}
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
            {chatrooms.map((room, index) => {
              const accent = ACCENT_COLORS[index % ACCENT_COLORS.length]
              return (
                <div
                  key={room.id}
                  onClick={() => handleOpenRoom(room.id)}
                  className="group bg-white rounded-xl p-6 shadow-sm border border-gray-100/80 hover:shadow-xl hover:shadow-gray-200/60 transition-all duration-300 flex flex-col justify-between h-48 cursor-pointer relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="material-symbols-outlined text-gray-300 text-lg">open_in_new</span>
                  </div>
                  <div>
                    <div className={`w-10 h-10 rounded-lg ${accent.bg} ${accent.text} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform text-lg`}>
                      {accent.icon}
                    </div>
                    <h3 className="text-base font-bold text-gray-900 leading-tight truncate pr-4">{room.name}</h3>
                    {room.last_message_preview && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-1">{room.last_message_preview}</p>
                    )}
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-gray-50">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${accent.badge}`}>
                      Analytics
                    </span>
                    <span className="text-xs text-gray-400">{timeAgo(room.created_at)}</span>
                  </div>
                </div>
              )
            })}

            {/* Start new thread card */}
            <div
              onClick={handleNewChat}
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
