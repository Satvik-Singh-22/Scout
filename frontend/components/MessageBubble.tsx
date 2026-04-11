'use client'
import { useState } from 'react'
import { Message } from '@/lib/api-client'
import ChainOfThought from './ChainOfThought'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, RotateCcw } from 'lucide-react'

export default function MessageBubble({
  message,
  persona,
  onResend
}: {
  message: Message
  persona: 'MANAGER' | 'DEVELOPER'
  onResend?: (content: string) => void
}) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'USER'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`flex group ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`w-full max-w-[85%] md:max-w-2xl px-4 py-3 rounded-2xl text-sm break-words relative
        ${isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
          }`}
      >
        {/* USER message stays plain text */}
        {isUser ? (
          <div className="whitespace-pre-wrap">
            {message.content}
          </div>
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Chain of Thought */}
        {!isUser && message.chain_of_thought && (
          <div className="mt-3">
            <ChainOfThought cot={message.chain_of_thought} />
          </div>
        )}

        {/* Action Bar */}
        <div className={`
          flex items-center gap-2 mt-2 pt-2 border-t opacity-0 group-hover:opacity-100 transition-opacity
          ${isUser ? 'border-indigo-500/30 justify-end' : 'border-gray-100 justify-start'}
        `}>
          <button
            onClick={handleCopy}
            className={`p-1.5 rounded-md hover:bg-black/5 transition-colors flex items-center gap-1.5 text-[10px] font-medium
              ${isUser ? 'text-indigo-100 hover:text-white' : 'text-gray-400 hover:text-gray-600'}`}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </button>

          {isUser && onResend && (
            <button
              onClick={() => onResend(message.content)}
              className="p-1.5 rounded-md hover:bg-black/5 transition-colors flex items-center gap-1.5 text-[10px] font-medium text-indigo-100 hover:text-white"
            >
              <RotateCcw size={12} />
              Resend
            </button>
          )}
        </div>
      </div>
    </div>
  )
}