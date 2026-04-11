'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getMe, User } from '@/lib/api-client'
import Chatroom from '@/components/Chatroom'
import { ArrowLeft } from 'lucide-react'

export default function ChatroomPage({ params }: { params: { chatroom_id: string } }) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [persona, setPersona] = useState<'MANAGER' | 'DEVELOPER' | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(u => {
        setUser(u)
        setPersona(u.persona as 'MANAGER' | 'DEVELOPER')
        setLoading(false)
      })
      .catch(() => {
        router.push('/login')
      })
  }, [router])

  if (loading) {
    return <div className="flex-1 flex items-center justify-center min-h-[calc(100vh-64px)] text-gray-500">Loading chat...</div>
  }

  if (!user || !persona) return null

  return (
    <div className="flex-1 bg-gray-50 flex flex-col h-[calc(100vh-64px)] relative">
      {/* Header */}
      <div className="h-14 border-b border-gray-200 bg-white shadow-sm flex items-center justify-between px-6 shrink-0 z-10 w-full relative">
        <div className="flex items-center gap-4">
          <Link href="/chat" className="p-1.5 text-gray-400 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <h2 className="text-sm font-bold text-gray-900 leading-tight">Chatroom: {params.chatroom_id}</h2>
            <span className="text-[10px] text-gray-500 font-medium">Secured Enterprise AI Core</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-gray-500">Mode:</span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${
            persona === 'MANAGER' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-900 text-white'
          }`}>
            {persona}
          </span>
        </div>
      </div>
      
      {/* Body */}
      <Chatroom 
        chatroomId={params.chatroom_id} 
        userPersona={persona} 
        onPersonaChange={(p) => setPersona(p)}
      />
    </div>
  )
}
