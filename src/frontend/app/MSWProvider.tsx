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
import { useEffect } from 'react'

export function MSWProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    async function initMSW() {
      // Only enable MSW when explicitly opted in via env variable.
      // When the real backend is running, mocks should be OFF.
      if (process.env.NEXT_PUBLIC_ENABLE_MOCKS === 'true') {
        const { worker } = await import('../mocks/browser')
        await worker.start({ onUnhandledRequest: 'bypass' })
        console.info('[MSW] Mock Service Worker enabled')
      }
    }
    initMSW()
  }, [])

  // Always render children immediately.
  // MSW initialises asynchronously in the background — it must never
  // block the render tree, because on the server useEffect never runs
  // and the old `return null` guard caused the entire page to prerender
  // as an empty tree, crashing Next.js's client-module manifest build.
  return <>{children}</>
}
