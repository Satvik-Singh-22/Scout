'use client'
import { useEffect, useState } from 'react'

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [mswReady, setMswReady] = useState(false)

  useEffect(() => {
    async function initMSW() {
      // Only enable MSW when explicitly opted in via env variable.
      // When the real backend is running, mocks should be OFF.
      if (process.env.NEXT_PUBLIC_ENABLE_MOCKS === 'true') {
        const { worker } = await import('../mocks/browser')
        await worker.start({ onUnhandledRequest: 'bypass' })
        console.info('[MSW] Mock Service Worker enabled')
        setMswReady(true)
      } else {
        setMswReady(true)
      }
    }
    initMSW()
  }, [])

  if (!mswReady) {
    // Prevent rendering while MSW is registering to avoid hydration mismatches
    return null
  }

  return <>{children}</>
}
