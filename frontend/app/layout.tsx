import type { Metadata } from 'next'
import localFont from 'next/font/local'

import './globals.css'
import { MSWProvider } from './MSWProvider'

const manrope = localFont({
  src: './fonts/GeistVF.woff',
  variable: '--font-manrope',
  display: 'swap',
})

const inter = localFont({
  src: './fonts/GeistMonoVF.woff',
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Scout',
  description: 'Enterprise AI Data Intelligence Platform',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${manrope.variable} ${inter.variable}`}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-on-surface font-body antialiased">
        <MSWProvider>{children}</MSWProvider>
      </body>
    </html>
  )
}