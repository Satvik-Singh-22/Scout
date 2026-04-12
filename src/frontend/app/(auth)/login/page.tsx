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
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/api-client'
import Link from 'next/link'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { user } = await login(email, password)
      if (user.role === 'PLATFORM_ADMIN') {
        router.push('/admin')
      } else {
        router.push('/dashboard')
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f4f2ff] px-4 py-8">
      {/* Outer card with purple glow border */}
      <div
        className={`w-full max-w-[960px] rounded-3xl shadow-2xl overflow-hidden transition-all duration-700 ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}
        style={{
          background: '#ffffff',
          boxShadow: '0 0 0 1px rgba(99, 91, 255, 0.12), 0 0 60px -10px rgba(99, 91, 255, 0.18), 0 25px 50px -12px rgba(0, 0, 0, 0.08)',
        }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[560px]">

          {/* ── LEFT PANEL — Brand / Marketing ── */}
          <div className="hidden lg:flex flex-col justify-between p-10 bg-[#fafaff] border-r border-gray-100 relative overflow-hidden">
            {/* Subtle accent gradient in corner */}
            <div className="absolute -top-20 -left-20 w-60 h-60 rounded-full opacity-[0.07]" style={{ background: 'radial-gradient(circle, #635bff 0%, transparent 70%)' }} />

            {/* Logo */}
            <div>
              <div className="flex items-center gap-3 mb-12">
                <img src="/scout_icon.svg" alt="Scout Logo" className="w-10 h-10 object-contain" />
                <span className="text-[17px] font-bold text-gray-900 tracking-tight">Scout Enterprise</span>
              </div>

              {/* Tagline */}
              <h2 className="text-[32px] leading-[1.2] font-bold text-gray-900 tracking-tight mb-4">
                The power of{' '}
                <span style={{ color: '#635bff' }}>intelligent</span>{' '}
                data queries.
              </h2>
              <p className="text-[15px] text-gray-500 leading-relaxed max-w-xs">
                Experience an enterprise-grade AI platform designed for natural language data exploration with full transparency.
              </p>
            </div>

            {/* Stats */}
            <div className="flex gap-4 mt-8">
              <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="text-2xl font-bold text-gray-900">99.9%</div>
                <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-1">Uptime SLA</div>
              </div>
              <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="text-2xl font-bold text-gray-900">100K+</div>
                <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-1">Queries Served</div>
              </div>
            </div>
          </div>

          {/* ── RIGHT PANEL — Login Form ── */}
          <div className="flex flex-col justify-center px-8 py-10 lg:px-12">
            {/* Mobile logo (visible only on small screens) */}
            <div className="flex items-center gap-3 mb-8 lg:hidden">
              <img src="/scout_icon.svg" alt="Scout Logo" className="w-9 h-9 object-contain" />
              <span className="text-base font-bold text-gray-900 tracking-tight">Scout</span>
            </div>

            <div>
              <h1 id="login-heading" className="text-[22px] font-bold text-gray-900 tracking-tight">
                Welcome back
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Enter your credentials to access your dashboard.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              {/* Error message */}
              {error && (
                <div
                  id="login-error"
                  className="flex items-center gap-2.5 p-3 rounded-xl text-sm"
                  style={{
                    background: '#fef2f2',
                    border: '1px solid #fecaca',
                    color: '#dc2626',
                  }}
                  role="alert"
                >
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  {error}
                </div>
              )}

              {/* Email */}
              <div>
                <label htmlFor="login-email" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  Work Email
                </label>
                <input
                  id="login-email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="you@company.com"
                  className="w-full px-4 py-2.5 rounded-xl text-sm text-gray-900 placeholder-gray-400 border border-gray-200 bg-gray-50/50 outline-none transition-all duration-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10 hover:border-gray-300"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="login-password" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 pr-10 rounded-xl text-sm text-gray-900 placeholder-gray-400 border border-gray-200 bg-gray-50/50 outline-none transition-all duration-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10 hover:border-gray-300"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      </svg>
                    ) : (
                      <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                className="w-full text-white font-semibold py-3 rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:ring-offset-2 hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: 'linear-gradient(135deg, #635bff 0%, #4f46e5 100%)',
                  boxShadow: '0 4px 14px rgba(99, 91, 255, 0.25)',
                }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Signing in…
                  </span>
                ) : (
                  'Sign In to Dashboard'
                )}
              </button>
            </form>

            {/* Link to register */}
            <p className="text-center text-sm text-gray-500 mt-8">
              Don&apos;t have an account?{' '}
              <Link
                href="/register"
                className="font-semibold hover:underline underline-offset-2 transition-colors"
                style={{ color: '#635bff' }}
              >
                Create one
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <p className="fixed bottom-4 text-center text-xs text-gray-400 w-full pointer-events-none">
        © {new Date().getFullYear()} Scout · Enterprise AI Platform
      </p>
    </div>
  )
}
