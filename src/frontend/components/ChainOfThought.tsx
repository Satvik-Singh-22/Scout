'use client'
import { useState } from 'react'
import { ChainOfThought as CoTType } from '@/lib/api-client'
import { ChevronDown, Play, Terminal, Database, ShieldCheck, ShieldAlert, ChevronRight } from 'lucide-react'

interface Props {
  cot: CoTType | null
  persona: 'EXECUTIVE' | 'TECHNICAL'
}

export default function ChainOfThought({ cot, persona }: Props) {
  const [open, setOpen] = useState(false)
  if (!cot) return null

  const isHighConfidence = cot.confidence === 'high'

  return (
    <div className={`border rounded-xl transition-all duration-200 overflow-hidden ${open ? 'border-gray-200 bg-gray-50/30' : 'border-gray-100 bg-white hover:border-gray-200'}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-gray-500 hover:text-gray-900 transition-colors group"
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown size={14} className="text-indigo-500" />
          ) : (
            <Play size={10} className="text-gray-400 fill-current group-hover:text-indigo-400" />
          )}
          <span className="text-[11px] font-bold uppercase tracking-wider">
            {open ? 'Hide reasoning' : 'Show reasoning'}
          </span>
        </div>
        
        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
          isHighConfidence 
            ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
            : 'bg-amber-50 text-amber-700 border-amber-100'
        }`}>
          {isHighConfidence ? <ShieldCheck size={12} /> : <ShieldAlert size={12} />}
          {isHighConfidence ? 'High Precision' : 'Limited Verification'}
        </div>
      </button>

      <div className={`
        overflow-hidden transition-all duration-300 ease-in-out
        ${open ? 'max-h-[1000px] border-t border-gray-100 py-4 px-4 opacity-100' : 'max-h-0 opacity-0'}
      `}>
        <div className="space-y-5">
          {/* Query intent */}
          <div className="flex items-start gap-3">
            <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
              <Terminal size={14} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Pipeline Intent</span>
              <p className="mt-0.5 text-xs font-medium text-gray-800">{cot.query_intent}</p>
            </div>
          </div>

          {/* Tables used */}
          {cot.tables_used && cot.tables_used.length > 0 && (
            <div className="flex items-start gap-3">
              <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
                <Database size={14} />
              </div>
              <div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Data Sources</span>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {cot.tables_used.map((t) => (
                    <span key={t} className="inline-flex items-center bg-white border border-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded shadow-sm font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* SQL executed — Only for TECHNICAL */}
          {persona === 'TECHNICAL' && cot.sql_executed && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">SQL Generation</span>
                <span className="text-[9px] text-gray-400">Read-only Execution</span>
              </div>
              <div className="relative group">
                <pre className="mt-1 bg-gray-900 text-green-400 text-[11px] p-4 rounded-xl overflow-x-auto font-mono leading-relaxed border border-gray-800 shadow-inner">
                  <code>{cot.sql_executed}</code>
                </pre>
              </div>
            </div>
          )}

          {/* RAG sources */}
          {cot.rag_chunks_used > 0 && (
            <div className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100/50">
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-1">Unstructured Context</span>
              <p className="text-xs text-indigo-900 leading-relaxed font-medium">
                Retrieved and synthesized information from {cot.rag_chunks_used} relevant document excerpts.
              </p>
            </div>
          )}

          {/* Agent path — Hidden for EXECUTIVEs */}
          {persona === 'TECHNICAL' && cot.agent_path && cot.agent_path.length > 0 && (
            <div>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-2">Agent Trace</span>
              <div className="flex items-center gap-1.5 flex-wrap">
                {cot.agent_path.map((agent, i) => (
                  <div key={agent} className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold bg-white border border-gray-200 text-gray-600 px-2 py-1 rounded shadow-sm capitalize">
                      {agent.replace('_', ' ')}
                    </span>
                    {i < cot.agent_path.length - 1 && <ChevronRight size={12} className="text-gray-300" />}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
