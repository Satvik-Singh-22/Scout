'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getMe, getDashboardCards } from '@/lib/api-client'
import type { User, DashboardCard as DashboardCardType } from '@/lib/api-client'
import DashboardCard from '@/components/DashboardCard'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [cards, setCards] = useState<DashboardCardType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getMe()
      .then(u => {
        setUser(u)
        // FIX: Always fetch cards; guard result with Array.isArray
        getDashboardCards()
          .then(fetched => setCards(Array.isArray(fetched) ? fetched : []))
          .catch(() => setCards([]))
          .finally(() => setLoading(false))
      })
      .catch(() => router.push('/login'))
  }, [router])

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto w-full">
        <div className="mb-8 h-10 bg-gray-200 rounded w-64 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl p-5 border border-gray-100 h-64 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
              <div className="h-40 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      <header className="mb-8 border-b border-gray-200 pb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Overview</h1>
            <span className={`px-2.5 py-0.5 rounded text-xs font-bold tracking-wider ${
              user.persona === 'MANAGER' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-900 text-white'
            }`}>
              {user.persona}
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">Welcome back, {user.name}. Here's your latest data overview.</p>
        </div>
      </header>

      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      {cards.length === 0 ? (
        <div className="py-16 text-center border-2 border-dashed border-gray-200 rounded-xl bg-white">
          <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-indigo-400 text-3xl">dashboard</span>
          </div>
          <h2 className="text-lg font-bold text-gray-600 mb-1">No dashboard cards yet</h2>
          <p className="text-sm text-gray-400 max-w-sm mx-auto">
            Ask the AI an analytical question in Chat, then pin the answer to your dashboard.
          </p>
          <button
            onClick={() => router.push('/chat')}
            className="mt-6 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-semibold text-sm hover:bg-indigo-700 transition-all"
          >
            Go to Chat
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map(card => (
            <DashboardCard key={card.id} card={card} />
          ))}
        </div>
      )}
    </div>
  )
}
