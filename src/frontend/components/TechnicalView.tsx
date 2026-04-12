'use client'
import { useState } from 'react'
import { ChainOfThought as CoTType } from '@/lib/api-client'

interface Props {
  content: string
  cot: CoTType | null
}

/**
 * Technical user facing view of an AI response.
 * Shows raw SQL, full schema details, RAG chunks, and technical agent path.
 */
export default function TechnicalView({ content, cot }: Props) {
  const [sqlCopied, setSqlCopied] = useState(false)

  const copySQL = async () => {
    if (!cot?.sql_executed) return
    await navigator.clipboard.writeText(cot.sql_executed)
    setSqlCopied(true)
    setTimeout(() => setSqlCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      {/* Raw response */}
      <div className="text-sm text-gray-800 leading-relaxed font-mono whitespace-pre-wrap">{content}</div>

      {cot && (
        <>
          {/* SQL Block */}
          {cot.sql_executed && (
            <div className="relative group">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">SQL Executed</span>
                <button
                  onClick={copySQL}
                  className="text-[10px] font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                >
                  {sqlCopied ? '✓ Copied' : 'Copy SQL'}
                </button>
              </div>
              <pre className="bg-gray-900 text-green-400 text-xs p-4 rounded-lg overflow-x-auto leading-relaxed">
                <code>{cot.sql_executed}</code>
              </pre>
            </div>
          )}

          {/* Technical details grid */}
          <div className="grid grid-cols-2 gap-3">
            {/* Query intent */}
            <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Query Intent</span>
              <div className="mt-1">
                <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded font-mono">
                  {cot.query_intent}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Confidence</span>
              <div className="mt-1">
                <span className={`inline-block text-xs px-2 py-0.5 rounded font-semibold ${cot.confidence === 'high' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                  {cot.confidence.toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Tables searched vs used */}
          <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Tables Searched</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {cot.tables_searched.map(t => (
                    <span key={t} className="inline-block bg-gray-200 text-gray-700 text-xs px-2 py-0.5 rounded font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Tables Used</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {cot.tables_used.map(t => (
                    <span key={t} className="inline-block bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* RAG info */}
          {cot.rag_chunks_used > 0 && (
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
              <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider">RAG Context</span>
              <p className="mt-1 text-xs text-amber-800">
                {cot.rag_chunks_used} vector chunks retrieved from semantic store
              </p>
            </div>
          )}

          {/* Agent pipeline */}
          <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Agent Pipeline</span>
            <div className="mt-2 flex items-center gap-1 flex-wrap font-mono">
              {cot.agent_path.map((agent, i) => (
                <span key={agent} className="flex items-center gap-1">
                  <span className="text-[11px] bg-white border border-gray-200 text-gray-700 px-2 py-0.5 rounded">
                    {agent}
                  </span>
                  {i < cot.agent_path.length - 1 && <span className="text-gray-300 text-xs">→</span>}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
