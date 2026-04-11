'use client'
import { useState } from 'react'
import { ChainOfThought as CoTType } from '@/lib/api-client'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Props {
  cot: CoTType | null
}

export default function ChainOfThought({ cot }: Props) {
  const [open, setOpen] = useState(false)
  if (!cot) return null

  return (
    <div className="mt-2 border border-gray-200 rounded-lg text-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="font-medium">Show reasoning</span>
        <span className="ml-auto text-xs">
          {cot.confidence === 'high' ? '🟢 High confidence' : '🔴 Low confidence'}
        </span>
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-3 border-t border-gray-100">
          {/* Query intent */}
          <div>
            <span className="text-xs font-semibold text-gray-400 uppercase">Query type</span>
            <div className="mt-1">
              <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded">
                {cot.query_intent}
              </span>
            </div>
          </div>

          {/* Tables used */}
          {cot.tables_used && cot.tables_used.length > 0 && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase">Data sources</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {cot.tables_used.map((t) => (
                  <span key={t} className="inline-block bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded font-mono">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Teams accessed — shown for Enterprise Analyst queries */}
          {cot.teams_accessed && cot.teams_accessed.length > 1 && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase">Teams accessed</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {cot.teams_accessed.map((t) => (
                  <span key={t} className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-0.5 rounded">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* SQL executed */}
          {cot.sql_executed && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase">SQL executed</span>
              <pre className="mt-1 bg-gray-900 text-green-400 text-xs p-3 rounded overflow-x-auto">
                <code>{cot.sql_executed}</code>
              </pre>
            </div>
          )}

          {/* RAG sources */}
          {cot.rag_chunks_used > 0 && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase">Text sources</span>
              <p className="mt-1 text-gray-600 text-xs">
                Searched customer reviews — {cot.rag_chunks_used} excerpts used.
              </p>
            </div>
          )}

          {/* Agent path */}
          {cot.agent_path && cot.agent_path.length > 0 && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase">Agent pipeline</span>
              <div className="mt-1 flex items-center gap-1 flex-wrap">
                {cot.agent_path.map((agent, i) => (
                  <span key={agent} className="flex items-center gap-1">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">{agent}</span>
                    {i < cot.agent_path.length - 1 && <span className="text-gray-400 text-xs">→</span>}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
