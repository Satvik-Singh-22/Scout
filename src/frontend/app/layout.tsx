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
        {/* Material Symbols Outlined — icon font for the entire app */}
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-on-surface font-body antialiased">
        <MSWProvider>{children}</MSWProvider>
      </body>
    </html>
  )
}