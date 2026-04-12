'use client'
import { useState } from 'react'
import { Message } from '@/lib/api-client'
import ChainOfThought from './ChainOfThought'
import ChartRenderer from './ChartRenderer'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, RotateCcw, Bot, User } from 'lucide-react'

export default function MessageBubble({
  message,
  persona,
  onResend
}: {
  message: Message
  persona: 'EXECUTIVE' | 'TECHNICAL'
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
    <div className={`flex flex-col mb-6 ${isUser ? 'items-end' : 'items-start'}`}>
      {/* Role Header */}
      {!isUser && (
        <div className="flex items-center gap-2 mb-1.5 ml-1">
          <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
            <Bot size={14} />
          </div>
          <span className="text-xs font-bold text-gray-900">Scout AI</span>
        </div>
      )}
      {isUser && (
        <div className="flex items-center gap-2 mb-1.5 mr-1">
          <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">You</span>
        </div>
      )}

      <div
        className={`w-full max-w-[85%] md:max-w-2xl px-4 py-4 rounded-2xl text-sm break-words relative transition-all duration-200
        ${isUser
            ? 'bg-indigo-600 text-white shadow-md rounded-tr-none'
            : 'bg-white border border-gray-200 text-gray-800 shadow-sm rounded-tl-none'
          }`}
      >
        {/* Assistant Card Header (Internal) */}
        {!isUser && (
          <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-2 border-b border-gray-100 pb-1">
            AI Response
          </div>
        )}

        {/* USER message stays plain text */}
        {isUser ? (
          <div className="whitespace-pre-wrap leading-relaxed">
            {message.content}
          </div>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:text-green-400">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Render Chart or Table if available */}
        {!isUser && message.chain_of_thought?.chart_type && (
          <div className="mt-4 mb-2 bg-gray-50 rounded-xl border border-gray-100 overflow-hidden">
             <div className="px-3 py-1.5 bg-gray-100/50 border-b border-gray-100 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
               Data Visualization
             </div>
             <div className="p-3">
               <ChartRenderer
                 chartType={message.chain_of_thought.chart_type}
                 sqlResults={message.chain_of_thought.sql_results}
                 height={message.chain_of_thought.chart_type === 'TABLE' ? 'auto' : 220}
               />
             </div>
          </div>
        )}

        {/* Chain of Thought */}
        {!isUser && message.chain_of_thought && (
          <div className="mt-4">
            <ChainOfThought
              cot={message.chain_of_thought}
              persona={persona}
            />
          </div>
        )}

        {/* Action Bar */}
        <div className={`
          flex items-center gap-2 mt-4 pt-3 border-t opacity-0 group-hover:opacity-100 transition-opacity
          ${isUser ? 'border-white/10 justify-end' : 'border-gray-50 justify-start'}
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