'use client'
import { useEffect, useState } from 'react'

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [mswReady, setMswReady] = useState(false)

  useEffect(() => {
    async function initMSW() {
      if (process.env.NODE_ENV === 'development') {
        const { worker } = await import('../mocks/browser')
        await worker.start({ onUnhandledRequest: 'bypass' })
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
