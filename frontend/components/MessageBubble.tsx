'use client'
import { Message } from '@/lib/api-client'
import ChainOfThought from './ChainOfThought'

export default function MessageBubble({ message, persona }: { message: Message, persona: 'MANAGER' | 'DEVELOPER' }) {
  const isUser = message.role === 'USER'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`w-full max-w-[85%] md:max-w-2xl px-4 py-3 rounded-2xl text-sm break-words ${isUser ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-800'}`}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        {!isUser && message.chain_of_thought && (
          <div className="mt-3">
            <ChainOfThought cot={message.chain_of_thought} />
          </div>
        )}
      </div>
    </div>
  )
}
