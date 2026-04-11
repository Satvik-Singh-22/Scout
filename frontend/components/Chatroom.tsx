'use client'
import { useState, useEffect, useRef } from 'react'
import { getMessages, streamMessage } from '@/lib/api-client'
import type { Message, ChainOfThought as CoTType } from '@/lib/api-client'
import MessageBubble from './MessageBubble'
import { Send } from 'lucide-react'
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface Props {
  chatroomId: string
  userPersona: 'MANAGER' | 'DEVELOPER'
  onPersonaChange?: (persona: 'MANAGER' | 'DEVELOPER') => void
}

function DevIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path d="M4 5L1 8l3 3M12 5l3 3-3 3M9 3l-2 10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  )
}

function MgrIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="4" width="12" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

export default function Chatroom({ chatroomId, userPersona, onPersonaChange }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getMessages(chatroomId).then(setMessages).catch(() => { })
  }, [chatroomId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSendQuery = (query: string) => {
    if (!query.trim() || isStreaming) return
    setIsStreaming(true)
    setStreamingContent('')

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'USER',
      content: query.trim(),
      chain_of_thought: null,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMsg])

    let accumulated = ''

    const stop = streamMessage(
      chatroomId,
      query.trim(),
      userPersona,
      (chunk) => {
        accumulated += chunk
        setStreamingContent(accumulated)
      },
      (cot: CoTType) => {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'ASSISTANT',
          content: accumulated,
          chain_of_thought: cot,
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, assistantMsg])
        setStreamingContent('')
        setIsStreaming(false)
      },
      (err) => {
        const errMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'ASSISTANT',
          content: `Error: ${err}`,
          chain_of_thought: null,
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, errMsg])
        setStreamingContent('')
        setIsStreaming(false)
      }
    )

    return () => stop()
  }

  const handleSend = () => {
    if (!input.trim() || isStreaming) return
    const query = input.trim()
    setInput('')
    handleSendQuery(query)
  }

  const personas = [
    {
      key: 'DEVELOPER' as const,
      label: 'Developer',
      desc: 'SQL, tables & technical details',
      icon: <DevIcon />,
      activeColor: 'text-emerald-600',
      activeBg: 'bg-white border border-gray-200',
    },
    {
      key: 'MANAGER' as const,
      label: 'Manager',
      desc: 'Plain English summaries',
      icon: <MgrIcon />,
      activeColor: 'text-violet-600',
      activeBg: 'bg-white border border-gray-200',
    },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-gray-400 mt-16">
            <p className="text-lg font-medium">Ask anything about your data</p>
            <p className="text-sm mt-1">Try: &quot;What is total payment volume this week?&quot;</p>
          </div>
        )}
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} persona={userPersona} onResend={handleSendQuery} />
        ))}
        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-2xl bg-white border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-800">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {streamingContent}
              </ReactMarkdown>
              <span className="inline-block w-1 h-4 bg-indigo-500 ml-1 animate-pulse" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="sticky bottom-0 border-t border-gray-200 px-6 py-4 bg-white">
        <div className="flex items-center gap-3">

          {/* Persona toggle */}
          <div className="flex items-center bg-gray-100 rounded-xl p-0.5 gap-0.5 shrink-0">
            {personas.map(p => {
              const isActive = userPersona === p.key
              return (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => onPersonaChange?.(p.key)}
                  disabled={isStreaming}
                  className={`
                    flex flex-col items-start gap-0.5 px-3 py-1.5 rounded-[10px]
                    text-left transition-all duration-200 disabled:opacity-50
                    ${isActive ? p.activeBg + ' shadow-sm' : 'hover:bg-white/50'}
                  `}
                >
                  <div className={`flex items-center gap-1.5 ${isActive ? p.activeColor : 'text-gray-400'}`}>
                    {p.icon}
                    <span className="text-xs font-semibold">{p.label}</span>
                  </div>
                  <span className={`text-[10px] leading-tight ${isActive ? 'text-gray-500' : 'text-gray-400'}`}>
                    {p.desc}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Input field */}
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask a question about your data..."
            disabled={isStreaming}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-40 transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}