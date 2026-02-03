'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { AuthLayout } from '@/components/auth/AuthLayout'
import { OAuthButtons, OrDivider } from '@/components/auth/OAuthButtons'

export const dynamic = 'force-dynamic'

export default function SignupPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { signUp } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      setLoading(false)
      return
    }

    try {
      const { error } = await signUp(email, password)

      if (error) {
        setError(error.message)
      } else {
        // Redirect to onboarding Step 2 (organization setup)
        router.push('/onboarding')
      }
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout variant="signup" showBackLink={false}>
      <div className="w-full max-w-lg relative">
        {/* Decorative gradient on the right */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-blue-100/50 to-transparent rounded-full blur-3xl -z-10 translate-x-1/2 -translate-y-1/4" />

        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-6 px-2">
          <span className="text-sm text-gray-400 font-medium">STEP 1 OF 3</span>
          <span className="text-sm font-semibold text-blue-500">33% COMPLETE</span>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-gray-200 rounded-full mb-10 overflow-hidden">
          <div className="h-full w-1/3 bg-blue-500 rounded-full transition-all duration-500" />
        </div>

        {/* Signup Card */}
        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 p-8 md:p-10">
          {/* Header */}
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            Create your mission control
          </h1>
          <p className="text-gray-500 mb-8">
            Start your 14-day free trial. No credit card required.
          </p>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl">
              {error}
            </div>
          )}

          {/* OAuth Buttons */}
          <OAuthButtons showSSO={false} loading={loading} />

          {/* Divider */}
          <OrDivider />

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="fullName" className="block text-sm font-semibold text-gray-700 mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                autoComplete="name"
                required
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                Work Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                placeholder="jane@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
              <p className="mt-2 text-xs text-gray-400">
                Must be at least 8 characters long.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2"
            >
              {loading ? 'Creating account...' : (
                <>
                  Next: Workspace Setup
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-gray-400">
          By signing up, you agree to our{' '}
          <Link href="/terms" className="text-blue-500 hover:underline">Terms of Service</Link>
          {' '}and{' '}
          <Link href="/privacy" className="text-blue-500 hover:underline">Privacy Policy</Link>.
        </p>
      </div>
    </AuthLayout>
  )
}