'use client'
import { useState, useEffect, useRef } from 'react'
import { getMessages, streamMessage } from '@/lib/api-client'
import type { Message, ChainOfThought as CoTType } from '@/lib/api-client'
import MessageBubble from './MessageBubble'
import { Send } from 'lucide-react'

interface Props {
  chatroomId: string
  userPersona: 'MANAGER' | 'DEVELOPER'
}

export default function Chatroom({ chatroomId, userPersona }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getMessages(chatroomId).then(setMessages).catch(() => {})
  }, [chatroomId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = () => {
    if (!input.trim() || isStreaming) return
    const query = input.trim()
    setInput('')
    setIsStreaming(true)
    setStreamingContent('')

    // Optimistically add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'USER',
      content: query,
      chain_of_thought: null,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMsg])

    let accumulated = ''

    const stop = streamMessage(
      chatroomId,
      query,
      (chunk) => {
        accumulated += chunk
        setStreamingContent(accumulated)
      },
      (cot: CoTType) => {
        // Done — add final assistant message
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

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-gray-400 mt-16">
            <p className="text-lg font-medium">Ask anything about your data</p>
            <p className="text-sm mt-1">Try: "What is total payment volume this week?"</p>
          </div>
        )}
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} persona={userPersona} />
        ))}
        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-2xl bg-white border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-800">
              {streamingContent}
              <span className="inline-block w-1 h-4 bg-indigo-500 ml-1 animate-pulse" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white">
        <div className="flex gap-3">
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
