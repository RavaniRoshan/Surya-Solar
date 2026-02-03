'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Bell, Rocket } from 'lucide-react'
import { ProgressBar } from '@/components/onboarding/ProgressBar'
import { PlanCards, defaultPlans } from '@/components/onboarding/PlanCards'

export const dynamic = 'force-dynamic'

export default function OnboardingStep3() {
    const [selectedPlan, setSelectedPlan] = useState('pro')
    const [emailAlerts, setEmailAlerts] = useState(true)
    const [loading, setLoading] = useState(false)

    const router = useRouter()

    const handleLaunch = async () => {
        setLoading(true)

        // TODO: Save preferences to backend
        // For now, just navigate to dashboard
        setTimeout(() => {
            router.push('/dashboard')
        }, 1000)
    }

    return (
        <div className="min-h-screen bg-[#0B1120]">
            {/* Top Navigation */}
            <nav className="flex items-center justify-between px-6 py-4">
                <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">✓</span>
                    </div>
                    <span className="font-bold text-white">ZERO-COMP</span>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-3xl mx-auto px-6 py-8">
                {/* Progress Bar */}
                <div className="mb-12">
                    <ProgressBar currentStep={3} totalSteps={3} label="Finalizing your account" />
                </div>

                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl md:text-5xl font-serif italic text-white mb-4">
                        You&apos;re almost there
                    </h1>
                    <p className="text-gray-400 text-lg max-w-lg mx-auto">
                        Configure your final environment preferences and choose your starting plan to launch your workspace.
                    </p>
                </div>

                {/* Subscription Selection */}
                <div className="mb-10">
                    <h2 className="text-lg font-bold text-white mb-6">Subscription Selection</h2>
                    <PlanCards
                        plans={defaultPlans}
                        selectedPlan={selectedPlan}
                        onSelect={setSelectedPlan}
                    />
                </div>

                {/* Notifications */}
                <div className="mb-10">
                    <h2 className="text-lg font-bold text-white mb-4">Notifications</h2>
                    <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-xl bg-gray-700 flex items-center justify-center">
                                    <Bell className="w-5 h-5 text-blue-400" />
                                </div>
                                <div>
                                    <div className="font-semibold text-white">Email Alerts</div>
                                    <div className="text-sm text-gray-400">
                                        Receive platform updates and critical data alerts via email
                                    </div>
                                </div>
                            </div>

                            {/* Toggle Switch */}
                            <button
                                type="button"
                                onClick={() => setEmailAlerts(!emailAlerts)}
                                className={`relative w-14 h-8 rounded-full transition-colors ${emailAlerts ? 'bg-blue-500' : 'bg-gray-600'
                                    }`}
                            >
                                <div
                                    className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-lg transition-transform ${emailAlerts ? 'translate-x-7' : 'translate-x-1'
                                        }`}
                                />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Launch Button */}
                <button
                    onClick={handleLaunch}
                    disabled={loading}
                    className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-bold text-lg rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/25 flex items-center justify-center gap-3"
                >
                    {loading ? (
                        'Launching...'
                    ) : (
                        <>
                            Launch Dashboard
                            <Rocket className="w-5 h-5" />
                        </>
                    )}
                </button>

                {/* Terms */}
                <p className="mt-6 text-center text-sm text-gray-500">
                    By clicking launch, you agree to the ZERO-COMP{' '}
                    <Link href="/terms" className="text-gray-400 hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link href="/privacy" className="text-gray-400 hover:underline">Privacy Policy</Link>.
                </p>
            </main>
        </div>
    )
}
