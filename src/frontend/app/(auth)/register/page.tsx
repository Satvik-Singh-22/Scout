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
import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { register, getTeams } from '@/lib/api-client'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const [teams, setTeams] = useState<{ id: string; name: string }[]>([])
  const [teamsLoading, setTeamsLoading] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    team_id: '',
    persona: 'EXECUTIVE',
    role: 'ANALYST'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    getTeams().then(data => {
      setTeams(data)
      if (data.length > 0) setFormData(prev => ({ ...prev, team_id: data[0].id }))
      setTeamsLoading(false)
    }).catch(() => setTeamsLoading(false))
  }, [])

  const updateField = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  // Password strength
  const passwordStrength = useMemo(() => {
    const p = formData.password
    if (!p) return { score: 0, label: '', color: '' }
    let score = 0
    if (p.length >= 8) score++
    if (p.length >= 12) score++
    if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++
    if (/\d/.test(p)) score++
    if (/[^a-zA-Z0-9]/.test(p)) score++

    if (score <= 2) return { score: 1, label: 'Weak', color: '#ef4444' }
    if (score <= 3) return { score: 2, label: 'Fair', color: '#f59e0b' }
    if (score <= 4) return { score: 3, label: 'Good', color: '#3b82f6' }
    return { score: 4, label: 'Strong', color: '#22c55e' }
  }, [formData.password])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters')
      setLoading(false)
      return
    }

    if (!formData.team_id) {
      setError('Please select a team')
      setLoading(false)
      return
    }

    try {
      await register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        persona: formData.persona,
        role: formData.role,
        team_id: formData.team_id,
      })
      router.push('/chat')
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

  const roleOptions = [
    { value: 'ANALYST', label: 'Analyst', description: 'Query data within your team' },
    { value: 'DATA_OWNER', label: 'Data Owner', description: 'Manage database connections' },
    { value: 'ENTERPRISE_ANALYST', label: 'Enterprise', description: 'Cross-team data access' },
  ]

  const personaOptions = [
    { value: 'EXECUTIVE', label: 'EXECUTIVE', icon: '📊', description: 'Charts & executive summaries' },
    { value: 'TECHNICAL', label: 'TECHNICAL', icon: '💻', description: 'Raw SQL & technical details' },
  ]

  const inputClasses = "w-full px-4 py-2.5 rounded-xl text-sm text-gray-900 placeholder-gray-400 border border-gray-200 bg-gray-50/50 outline-none transition-all duration-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10 hover:border-gray-300"

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f4f2ff] px-4 py-8">
      {/* Outer card with purple glow border */}
      <div
        className={`w-full max-w-[1040px] rounded-3xl shadow-2xl overflow-hidden transition-all duration-700 ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}
        style={{
          background: '#ffffff',
          boxShadow: '0 0 0 1px rgba(99, 91, 255, 0.12), 0 0 60px -10px rgba(99, 91, 255, 0.18), 0 25px 50px -12px rgba(0, 0, 0, 0.08)',
        }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr]">

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
              <h2 className="text-[30px] leading-[1.2] font-bold text-gray-900 tracking-tight mb-4">
                Join the{' '}
                <span style={{ color: '#635bff' }}>future</span>{' '}
                of data intelligence.
              </h2>
              <p className="text-[15px] text-gray-500 leading-relaxed max-w-xs">
                Create your account to start asking natural language questions about your enterprise data.
              </p>
            </div>

            {/* Stats */}
            <div className="flex gap-4 mt-8">
              <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="text-2xl font-bold text-gray-900">5+</div>
                <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-1">Team Roles</div>
              </div>
              <div className="flex-1 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="text-2xl font-bold text-gray-900">12</div>
                <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-1">Data Tables</div>
              </div>
            </div>
          </div>

          {/* ── RIGHT PANEL — Register Form ── */}
          <div className="flex flex-col justify-center px-8 py-8 lg:px-10 lg:py-8 overflow-y-auto" style={{ maxHeight: '100vh' }}>
            {/* Mobile logo */}
            <div className="flex items-center gap-3 mb-6 lg:hidden">
              <img src="/scout_icon.svg" alt="Scout Logo" className="w-9 h-9 object-contain" />
              <span className="text-base font-bold text-gray-900 tracking-tight">Scout</span>
            </div>

            <div>
              <h1 id="register-heading" className="text-[22px] font-bold text-gray-900 tracking-tight">
                Create your account
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Join Scout to start querying your enterprise data.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {/* Error message */}
              {error && (
                <div
                  id="register-error"
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

              {/* Name + Email — side by side */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="register-name" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Full Name
                  </label>
                  <input
                    id="register-name"
                    type="text"
                    required
                    autoComplete="name"
                    placeholder="Jane Doe"
                    className={inputClasses}
                    value={formData.name}
                    onChange={e => updateField('name', e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="register-email" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Work Email
                  </label>
                  <input
                    id="register-email"
                    type="email"
                    required
                    autoComplete="email"
                    placeholder="jane@company.com"
                    className={inputClasses}
                    value={formData.email}
                    onChange={e => updateField('email', e.target.value)}
                  />
                </div>
              </div>

              {/* Password with strength indicator */}
              <div>
                <label htmlFor="register-password" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="register-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoComplete="new-password"
                    placeholder="Min. 8 characters"
                    minLength={8}
                    className={`${inputClasses} pr-10`}
                    value={formData.password}
                    onChange={e => updateField('password', e.target.value)}
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
                {/* Password strength bar */}
                {formData.password.length > 0 && (
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex-1 flex gap-1">
                      {[1, 2, 3, 4].map(i => (
                        <div
                          key={i}
                          className="h-1 flex-1 rounded-full transition-all duration-300"
                          style={{
                            background: i <= passwordStrength.score
                              ? passwordStrength.color
                              : '#e5e7eb',
                          }}
                        />
                      ))}
                    </div>
                    <span
                      className="text-[11px] font-semibold transition-colors duration-300"
                      style={{ color: passwordStrength.color }}
                    >
                      {passwordStrength.label}
                    </span>
                  </div>
                )}
              </div>

              {/* Team */}
              <div>
                <label htmlFor="register-team" className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  Team
                </label>
                {teamsLoading ? (
                  <div className="w-full px-4 py-2.5 rounded-xl text-sm text-gray-400 bg-gray-50 border border-gray-200 flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Loading teams…
                  </div>
                ) : teams.length === 0 ? (
                  <div className="w-full px-4 py-2.5 rounded-xl text-sm bg-red-50 border border-red-200 text-red-600">
                    No teams available. Contact your admin.
                  </div>
                ) : (
                  <select
                    id="register-team"
                    required
                    className={`${inputClasses} cursor-pointer`}
                    value={formData.team_id}
                    onChange={e => updateField('team_id', e.target.value)}
                  >
                    {teams.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                )}
              </div>

              {/* Role selector */}
              <div>
                <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Role</label>
                <div className="grid grid-cols-3 gap-2">
                  {roleOptions.map(option => {
                    const isSelected = formData.role === option.value
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => updateField('role', option.value)}
                        className={`relative p-3 rounded-xl text-left transition-all duration-200 border ${isSelected
                          ? 'bg-indigo-50 border-indigo-300 ring-1 ring-indigo-400/30'
                          : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          }`}
                      >
                        <span className={`block text-xs font-semibold ${isSelected ? 'text-indigo-700' : 'text-gray-700'}`}>
                          {option.label}
                        </span>
                        <span className={`block text-[10px] mt-0.5 leading-tight ${isSelected ? 'text-indigo-500' : 'text-gray-400'}`}>
                          {option.description}
                        </span>
                        {isSelected && (
                          <div className="absolute top-2 right-2">
                            <svg className="w-3.5 h-3.5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Persona selector */}
              <div>
                <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Persona</label>
                <div className="grid grid-cols-2 gap-2">
                  {personaOptions.map(option => {
                    const isSelected = formData.persona === option.value
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => updateField('persona', option.value)}
                        className={`relative p-3 rounded-xl text-left transition-all duration-200 border ${isSelected
                          ? 'bg-indigo-50 border-indigo-300 ring-1 ring-indigo-400/30'
                          : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="text-base">{option.icon}</span>
                          <span>
                            <span className={`block text-xs font-semibold ${isSelected ? 'text-indigo-700' : 'text-gray-700'}`}>
                              {option.label}
                            </span>
                            <span className={`block text-[10px] ${isSelected ? 'text-indigo-500' : 'text-gray-400'}`}>
                              {option.description}
                            </span>
                          </span>
                        </span>
                        {isSelected && (
                          <div className="absolute top-2 right-2">
                            <svg className="w-3.5 h-3.5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Submit */}
              <button
                id="register-submit"
                type="submit"
                disabled={loading}
                className="w-full text-white font-semibold py-3 rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:ring-offset-2 hover:shadow-lg active:scale-[0.98] mt-1"
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
                    Creating account…
                  </span>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            {/* Link to login */}
            <p className="text-center text-sm text-gray-500 mt-6">
              Already have an account?{' '}
              <Link
                href="/login"
                className="font-semibold hover:underline underline-offset-2 transition-colors"
                style={{ color: '#635bff' }}
              >
                Sign in
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
