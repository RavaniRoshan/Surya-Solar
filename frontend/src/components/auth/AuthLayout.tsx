'use client'

import Link from 'next/link'
import { ReactNode } from 'react'

interface AuthLayoutProps {
    children: ReactNode
    showBackLink?: boolean
    variant?: 'login' | 'signup' | 'onboarding'
}

export function AuthLayout({ children, showBackLink = true, variant = 'login' }: AuthLayoutProps) {
    const isOnboarding = variant === 'onboarding'

    return (
        <div className={`min-h-screen ${isOnboarding ? 'bg-[#0B1120]' : 'bg-[#FAF9F7]'}`}>
            {/* Top Navigation */}
            <nav className="flex items-center justify-between px-6 py-4">
                {showBackLink && !isOnboarding ? (
                    <Link
                        href="/"
                        className="text-sm text-gray-500 hover:text-gray-700 transition-colors flex items-center gap-1"
                    >
                        ← Back to home
                    </Link>
                ) : (
                    <div className="flex items-center space-x-2">
                        <div className={`w-8 h-8 rounded-lg ${isOnboarding ? 'bg-blue-500' : 'bg-gray-900'} flex items-center justify-center`}>
                            <span className="text-white font-bold text-sm">Z</span>
                        </div>
                        <span className={`font-bold ${isOnboarding ? 'text-white' : 'text-gray-900'}`}>ZERO-COMP</span>
                    </div>
                )}

                {variant === 'signup' || variant === 'onboarding' ? (
                    <div className="flex items-center space-x-3">
                        <span className={`text-sm ${isOnboarding ? 'text-gray-400' : 'text-gray-500'}`}>
                            Already have an account?
                        </span>
                        <Link
                            href="/auth/login"
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${isOnboarding
                                    ? 'bg-gray-800 text-white hover:bg-gray-700 border border-gray-700'
                                    : 'bg-white border border-gray-200 text-gray-900 hover:bg-gray-50'
                                }`}
                        >
                            Log in
                        </Link>
                    </div>
                ) : null}
            </nav>

            {/* Main Content */}
            <main className="flex flex-col items-center justify-center px-4 py-8">
                {/* Logo for login page */}
                {variant === 'login' && (
                    <div className="flex items-center space-x-2 mb-8">
                        <div className="w-10 h-10 rounded-lg bg-gray-900 flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                                <circle cx="12" cy="12" r="4" />
                                {[...Array(8)].map((_, i) => (
                                    <rect
                                        key={i}
                                        x="11"
                                        y="1"
                                        width="2"
                                        height="4"
                                        rx="1"
                                        transform={`rotate(${i * 45} 12 12)`}
                                    />
                                ))}
                            </svg>
                        </div>
                        <span className="font-bold text-xl text-gray-900">ZERO-COMP</span>
                    </div>
                )}

                {children}
            </main>

            {/* Footer for login page */}
            {variant === 'login' && (
                <footer className="fixed bottom-0 left-0 right-0 py-6 text-center">
                    <div className="flex items-center justify-center space-x-6 text-xs text-gray-400 uppercase tracking-wider">
                        <Link href="/privacy" className="hover:text-gray-600 transition-colors">Privacy Policy</Link>
                        <Link href="/terms" className="hover:text-gray-600 transition-colors">Terms of Service</Link>
                        <Link href="/security" className="hover:text-gray-600 transition-colors">Security</Link>
                    </div>
                </footer>
            )}
        </div>
    )
}
