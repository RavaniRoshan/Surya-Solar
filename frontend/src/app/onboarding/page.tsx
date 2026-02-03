'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { ProgressBar } from '@/components/onboarding/ProgressBar'
import { UseCasePills } from '@/components/onboarding/UseCasePills'

export const dynamic = 'force-dynamic'

const industries = [
    'Aerospace & Defense',
    'Telecommunications',
    'Energy & Utilities',
    'Government',
    'Research & Academia',
    'Financial Services',
    'Healthcare',
    'Other'
]

const useCaseOptions = [
    'Real-time Alerts',
    'Data Analysis',
    'SLA Compliance',
    'Network Resilience',
    'System Health'
]

export default function OnboardingPage() {
    const [companyName, setCompanyName] = useState('')
    const [industry, setIndustry] = useState('')
    const [useCases, setUseCases] = useState<string[]>([])
    const [loading, setLoading] = useState(false)

    const router = useRouter()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)

        // TODO: Save organization data to backend
        // For now, just navigate to step 3
        setTimeout(() => {
            router.push('/onboarding/step-3')
        }, 500)
    }

    const handleBack = () => {
        router.back()
    }

    return (
        <div className="min-h-screen bg-[#0B1120]">
            {/* Top Navigation */}
            <nav className="flex items-center justify-between px-6 py-4">
                <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">Z</span>
                    </div>
                    <span className="font-bold text-white">ZERO-COMP</span>
                </div>

                <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-400">Already have an account?</span>
                    <Link
                        href="/auth/login"
                        className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-800 text-white hover:bg-gray-700 border border-gray-700 transition-all"
                    >
                        Log In
                    </Link>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-2xl mx-auto px-6 py-12">
                {/* Header with Progress */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">ONBOARDING</span>
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-6">Organization Setup</h1>
                    <ProgressBar currentStep={2} totalSteps={3} />
                </div>

                {/* Form Card */}
                <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-8">
                    <h2 className="text-xl font-bold text-white mb-2">
                        Tell us about your organization
                    </h2>
                    <p className="text-gray-400 mb-8">
                        We&apos;ll use this information to customize your dashboard experience.
                    </p>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Company Name */}
                        <div>
                            <label htmlFor="companyName" className="block text-sm font-semibold text-gray-300 mb-2">
                                Company Name
                            </label>
                            <input
                                id="companyName"
                                name="companyName"
                                type="text"
                                placeholder="e.g. Acme Aerospace"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                            />
                        </div>

                        {/* Industry */}
                        <div>
                            <label htmlFor="industry" className="block text-sm font-semibold text-gray-300 mb-2">
                                Industry
                            </label>
                            <div className="relative">
                                <select
                                    id="industry"
                                    name="industry"
                                    value={industry}
                                    onChange={(e) => setIndustry(e.target.value)}
                                    className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all cursor-pointer"
                                >
                                    <option value="" className="bg-gray-900">Select an industry</option>
                                    {industries.map((ind) => (
                                        <option key={ind} value={ind} className="bg-gray-900">{ind}</option>
                                    ))}
                                </select>
                                <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Use Cases */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-300 mb-3">
                                What is your primary use case?
                            </label>
                            <UseCasePills
                                options={useCaseOptions}
                                selected={useCases}
                                onChange={setUseCases}
                            />
                        </div>

                        {/* Navigation Buttons */}
                        <div className="flex items-center justify-between pt-4">
                            <button
                                type="button"
                                onClick={handleBack}
                                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                Back
                            </button>

                            <button
                                type="submit"
                                disabled={loading}
                                className="px-8 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Saving...' : 'Continue'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Help Card */}
                <div className="mt-8 bg-gray-800/30 rounded-2xl border border-gray-700/50 p-6 flex items-center justify-center gap-4">
                    <div className="flex -space-x-2">
                        <div className="w-8 h-8 rounded-full bg-gray-600 border-2 border-gray-800"></div>
                        <div className="w-8 h-8 rounded-full bg-gray-500 border-2 border-gray-800"></div>
                    </div>
                    <p className="text-gray-400 text-sm">
                        Need help setting up?{' '}
                        <Link href="/contact" className="text-blue-400 hover:underline">
                            Chat with an expert
                        </Link>
                    </p>
                </div>
            </main>
        </div>
    )
}
