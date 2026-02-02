'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import {
    Rocket,
    Mail,
    Clock,
    CheckCircle,
    Sparkles,
    ArrowLeft
} from 'lucide-react'

export default function BetaWaitingPage() {
    const [userEmail, setUserEmail] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchUser = async () => {
            const supabase = createClient()
            const { data: { user } } = await supabase.auth.getUser()
            if (user?.email) {
                setUserEmail(user.email)
            }
            setLoading(false)
        }
        fetchUser()
    }, [])

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
            {/* Background gradient */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl" />
            </div>

            <div className="relative w-full max-w-lg">
                {/* Card */}
                <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl overflow-hidden shadow-2xl">
                    {/* Header */}
                    <div className="p-6 border-b border-[#2a2a3a] flex items-center justify-between">
                        <Link href="/" className="flex items-center space-x-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center">
                                <span className="text-sm font-bold text-white">Z</span>
                            </div>
                            <span className="text-lg font-semibold text-white">ZERO-COMP</span>
                        </Link>
                        <span className="px-3 py-1 bg-amber-500/20 border border-amber-500/30 rounded-full text-amber-400 text-xs font-medium">
                            BETA
                        </span>
                    </div>

                    {/* Content */}
                    <div className="p-8 text-center">
                        {/* Icon */}
                        <div className="relative w-20 h-20 mx-auto mb-6">
                            <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-cyan-500 rounded-2xl opacity-20 blur-xl animate-pulse" />
                            <div className="relative w-20 h-20 bg-gradient-to-br from-purple-600 to-cyan-500 rounded-2xl flex items-center justify-center">
                                <Rocket className="w-10 h-10 text-white" />
                            </div>
                            <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                                <CheckCircle className="w-4 h-4 text-white" />
                            </div>
                        </div>

                        {/* Title */}
                        <h1 className="text-2xl font-bold text-white mb-2">
                            You&apos;re on the Beta List!
                        </h1>

                        <p className="text-gray-400 mb-6">
                            Thank you for registering for ZERO-COMP beta access.
                        </p>

                        {/* User Email */}
                        {userEmail && (
                            <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-4 mb-6">
                                <div className="flex items-center justify-center space-x-3">
                                    <Mail className="w-5 h-5 text-purple-400" />
                                    <span className="text-white font-medium">{userEmail}</span>
                                </div>
                            </div>
                        )}

                        {/* Info Card */}
                        <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-6 mb-6 text-left">
                            <div className="flex items-start space-x-3">
                                <Sparkles className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <h3 className="font-semibold text-white mb-2">What happens next?</h3>
                                    <ul className="space-y-2 text-sm text-gray-400">
                                        <li className="flex items-center space-x-2">
                                            <Clock className="w-4 h-4 text-cyan-400" />
                                            <span>We&apos;re preparing your beta access</span>
                                        </li>
                                        <li className="flex items-center space-x-2">
                                            <Mail className="w-4 h-4 text-cyan-400" />
                                            <span>You&apos;ll receive an email when ready</span>
                                        </li>
                                        <li className="flex items-center space-x-2">
                                            <CheckCircle className="w-4 h-4 text-cyan-400" />
                                            <span>Early access to solar predictions</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Expected Timeline */}
                        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500 mb-6">
                            <Clock className="w-4 h-4" />
                            <span>Expected access: Within the next few days</span>
                        </div>

                        {/* Action Buttons */}
                        <div className="space-y-3">
                            <Link
                                href="/"
                                className="flex items-center justify-center space-x-2 w-full py-3 bg-[#1a1a24] hover:bg-[#222230] border border-[#2a2a3a] rounded-xl text-white transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                <span>Back to Home</span>
                            </Link>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-4 border-t border-[#2a2a3a] bg-[#0a0a0f]/50">
                        <p className="text-center text-xs text-gray-600">
                            Questions? Contact us at{' '}
                            <a href="mailto:support@zero-comp.com" className="text-purple-400 hover:underline">
                                support@zero-comp.com
                            </a>
                        </p>
                    </div>
                </div>

                {/* Bottom text */}
                <p className="text-center text-sm text-gray-600 mt-6">
                    © 2024 ZERO-COMP Solar Weather Prediction
                </p>
            </div>
        </div>
    )
}
