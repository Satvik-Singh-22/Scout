'use client'
import { useState, useEffect } from 'react'
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
    persona: 'MANAGER',
    role: 'ANALYST'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    getTeams().then(data => {
      setTeams(data)
      if (data.length > 0) setFormData(prev => ({ ...prev, team_id: data[0].id }))
      setTeamsLoading(false)
    }).catch(() => setTeamsLoading(false))
  }, [])

  const updateField = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await register(formData)
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
    { value: 'ENTERPRISE_ANALYST', label: 'Enterprise Analyst', description: 'Cross-team data access' },
  ]

  const personaOptions = [
    { value: 'MANAGER', label: 'Manager', description: 'Charts & executive summaries' },
    { value: 'DEVELOPER', label: 'Developer', description: 'Raw SQL & technical details' },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-100 rounded-full opacity-40 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-50 rounded-full opacity-50 blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg">
        {/* Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {/* Logo & heading */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-5 shadow-lg shadow-indigo-200 transition-transform hover:scale-105">
              <span className="text-white text-2xl font-bold tracking-tight">B</span>
            </div>
            <h1 id="register-heading" className="text-2xl font-bold text-gray-900 tracking-tight">
              Create your account
            </h1>
            <p className="text-gray-500 text-sm mt-2">
              Join Banquoite to start querying your enterprise data
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Error message */}
            {error && (
              <div
                id="register-error"
                className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg"
                role="alert"
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            {/* Full Name */}
            <div>
              <label htmlFor="register-name" className="block text-sm font-medium text-gray-700 mb-1.5">
                Full Name
              </label>
              <input
                id="register-name"
                type="text"
                required
                autoComplete="name"
                placeholder="Jane Doe"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 bg-white transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 hover:border-gray-400"
                value={formData.name}
                onChange={e => updateField('name', e.target.value)}
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="register-email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Email address
              </label>
              <input
                id="register-email"
                type="email"
                required
                autoComplete="email"
                placeholder="jane@company.com"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 bg-white transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 hover:border-gray-400"
                value={formData.email}
                onChange={e => updateField('email', e.target.value)}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="register-password" className="block text-sm font-medium text-gray-700 mb-1.5">
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
                  className="w-full px-4 py-2.5 pr-10 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 bg-white transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 hover:border-gray-400"
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
            </div>

            {/* Team */}
            <div>
              <label htmlFor="register-team" className="block text-sm font-medium text-gray-700 mb-1.5">
                Team
              </label>
              {teamsLoading ? (
                <div className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm text-gray-400 bg-gray-50">
                  Loading teams…
                </div>
              ) : teams.length === 0 ? (
                <div className="w-full px-4 py-2.5 border border-red-200 rounded-lg text-sm text-red-500 bg-red-50">
                  No teams available. Contact your admin.
                </div>
              ) : (
                <select
                  id="register-team"
                  required
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 hover:border-gray-400"
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
              <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
              <div className="grid grid-cols-3 gap-2">
                {roleOptions.map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('role', option.value)}
                    className={`relative p-3 rounded-lg border text-left transition-all ${
                      formData.role === option.value
                        ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500'
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <span className={`block text-sm font-medium ${
                      formData.role === option.value ? 'text-indigo-700' : 'text-gray-700'
                    }`}>
                      {option.label}
                    </span>
                    <span className={`block text-xs mt-0.5 ${
                      formData.role === option.value ? 'text-indigo-500' : 'text-gray-400'
                    }`}>
                      {option.description}
                    </span>
                    {formData.role === option.value && (
                      <div className="absolute top-2 right-2">
                        <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Persona selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Persona</label>
              <div className="grid grid-cols-2 gap-2">
                {personaOptions.map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('persona', option.value)}
                    className={`relative p-3 rounded-lg border text-left transition-all ${
                      formData.persona === option.value
                        ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500'
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span className="text-lg">
                        {option.value === 'MANAGER' ? '📊' : '💻'}
                      </span>
                      <span>
                        <span className={`block text-sm font-medium ${
                          formData.persona === option.value ? 'text-indigo-700' : 'text-gray-700'
                        }`}>
                          {option.label}
                        </span>
                        <span className={`block text-xs ${
                          formData.persona === option.value ? 'text-indigo-500' : 'text-gray-400'
                        }`}>
                          {option.description}
                        </span>
                      </span>
                    </span>
                    {formData.persona === option.value && (
                      <div className="absolute top-2 right-2">
                        <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <button
              id="register-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white font-medium py-2.5 rounded-lg hover:bg-indigo-700 active:bg-indigo-800 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 shadow-sm hover:shadow mt-2"
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
              className="text-indigo-600 font-medium hover:text-indigo-700 hover:underline transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 mt-6">
          © {new Date().getFullYear()} Banquoite Inc. · Enterprise AI Platform
        </p>
      </div>
    </div>
  )
}
