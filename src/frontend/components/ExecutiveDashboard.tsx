/**
 * Copyright 2026 The SCOUT Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client'
import { ChainOfThought as CoTType } from '@/lib/api-client'

interface Props {
  content: string
  cot: CoTType | null
}

/**
 * Executive-facing view of an AI response.
 * Shows executive summary with key metrics highlighted and simplified visuals.
 */
export default function ExecutiveDashboard({ content, cot }: Props) {
  return (
    <div className="space-y-4">
      {/* Executive summary */}
      <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{content}</div>

      {/* Key metrics callout */}
      {cot && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-indigo-700">{cot.tables_used.length}</div>
            <div className="text-[10px] font-semibold text-indigo-500 uppercase tracking-wider">Data Sources</div>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-emerald-700">
              {cot.confidence === 'high' ? '✓ High' : '⚠ Low'}
            </div>
            <div className="text-[10px] font-semibold text-emerald-500 uppercase tracking-wider">Confidence</div>
          </div>
          <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-purple-700">{cot.teams_accessed.length}</div>
            <div className="text-[10px] font-semibold text-purple-500 uppercase tracking-wider">
              Team{cot.teams_accessed.length !== 1 ? 's' : ''} Queried
            </div>
          </div>
        </div>
      )}

      {/* Simplified agent path */}
      {cot && cot.agent_path.length > 0 && (
        <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Analysis Pipeline</span>
          <div className="mt-2 flex items-center gap-1 flex-wrap">
            {cot.agent_path.map((step, i) => (
              <span key={step} className="flex items-center gap-1">
                <span className="text-xs bg-white border border-gray-200 text-gray-600 px-2 py-0.5 rounded font-medium capitalize">
                  {step.replace(/_/g, ' ')}
                </span>
                {i < cot.agent_path.length - 1 && <span className="text-gray-300 text-xs">→</span>}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
