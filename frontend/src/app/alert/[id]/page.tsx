'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
    AlertTriangle,
    ExternalLink,
    HelpCircle,
    Linkedin,
    Radio
} from 'lucide-react'

// Mock alert data - in production, fetch from API
const mockAlert = {
    id: '1',
    class: 'X1.2',
    activeRegion: 'AR 3664',
    timestamp: '16:42:01 UTC',
    status: 'ACTIVE',
    severity: 'critical' as const,
    impact: {
        radioBlackout: '90% chance of HF signal degradation across sunlit hemisphere.',
        satellites: 'Low Earth Orbit (LEO) assets may experience increased drag and charging.',
        duration: 'Intermittent disruptions expected for the next 24-48 hours.'
    }
}

export default function AlertDetailPage() {
    const [alert] = useState(mockAlert)
    const [fluxData, setFluxData] = useState<number[]>([])

    // Generate animated flux data
    useEffect(() => {
        const generateFluxData = () => {
            const data = []
            for (let i = 0; i < 30; i++) {
                data.push(20 + Math.sin(i * 0.3) * 15 + Math.random() * 10)
            }
            return data
        }

        setFluxData(generateFluxData())

        const interval = setInterval(() => {
            setFluxData(prev => {
                const newData = [...prev.slice(1), 20 + Math.sin(prev.length * 0.3) * 15 + Math.random() * 10]
                return newData
            })
        }, 1000)

        return () => clearInterval(interval)
    }, [])

    // SVG path for flux chart
    const fluxPath = fluxData.length > 0
        ? `M 0 ${80 - fluxData[0]} ` + fluxData.map((v, i) => `L ${i * 20} ${80 - v}`).join(' ')
        : ''

    return (
        <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
            <div className="w-full max-w-xl">
                {/* Alert Card */}
                <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl overflow-hidden">
                    {/* Header */}
                    <div className="p-4 flex items-center justify-between border-b border-[#2a2a3a]">
                        <Link href="/" className="flex items-center space-x-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center">
                                <span className="text-sm font-bold text-white">Z</span>
                            </div>
                            <span className="text-lg font-semibold text-white">ZERO-COMP</span>
                        </Link>
                        <span className="px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-full text-red-400 text-xs font-medium flex items-center space-x-1">
                            <span className="w-1.5 h-1.5 bg-red-400 rounded-full animate-pulse" />
                            <span>CRITICAL ALERT</span>
                        </span>
                    </div>

                    {/* Alert Content */}
                    <div className="p-8 text-center">
                        {/* Icon */}
                        <div className="w-16 h-16 bg-red-500/20 rounded-xl mx-auto flex items-center justify-center mb-6">
                            <AlertTriangle className="w-8 h-8 text-red-400" />
                        </div>

                        {/* Title */}
                        <h1 className="text-3xl font-bold text-white mb-2">
                            X-Class Flare Detected
                        </h1>

                        {/* Subtitle */}
                        <p className="text-lg text-gray-400 mb-4">
                            Magnitude: <span className="text-red-400 font-semibold">{alert.class}</span> | Active Region: <span className="text-white font-semibold">{alert.activeRegion}</span>
                        </p>

                        {/* Timestamp & Status */}
                        <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 mb-8">
                            <span>TIMESTAMP: {alert.timestamp}</span>
                            <span>•</span>
                            <span>STATUS: <span className="text-green-400">{alert.status}</span></span>
                        </div>

                        {/* Impact Summary */}
                        <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-6 text-left mb-8">
                            <div className="flex items-center space-x-2 mb-4">
                                <Radio className="w-4 h-4 text-cyan-400" />
                                <h3 className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                                    Impact Summary
                                </h3>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-start space-x-3">
                                    <span className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0" />
                                    <div>
                                        <p className="font-medium text-white">Radio Blackout Probability</p>
                                        <p className="text-sm text-gray-400">{alert.impact.radioBlackout}</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-3">
                                    <span className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0" />
                                    <div>
                                        <p className="font-medium text-white">Affected Satellites</p>
                                        <p className="text-sm text-gray-400">{alert.impact.satellites}</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-3">
                                    <span className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0" />
                                    <div>
                                        <p className="font-medium text-white">Estimated Duration</p>
                                        <p className="text-sm text-gray-400">{alert.impact.duration}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Real-time Spectral Flux */}
                        <div className="mb-8">
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-xs uppercase tracking-wider text-gray-500">Real-Time Spectral Flux</span>
                                <span className="text-xs text-red-400">LIVE FROM L1 NODE</span>
                            </div>

                            <div className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-4 h-32 overflow-hidden">
                                <svg className="w-full h-full" viewBox="0 0 580 100" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="fluxGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                            <stop offset="0%" stopColor="rgba(6, 182, 212, 0.3)" />
                                            <stop offset="100%" stopColor="rgba(6, 182, 212, 0)" />
                                        </linearGradient>
                                    </defs>

                                    {/* Grid lines */}
                                    <line x1="0" y1="25" x2="580" y2="25" stroke="#2a2a3a" strokeWidth="0.5" />
                                    <line x1="0" y1="50" x2="580" y2="50" stroke="#2a2a3a" strokeWidth="0.5" />
                                    <line x1="0" y1="75" x2="580" y2="75" stroke="#2a2a3a" strokeWidth="0.5" />

                                    {/* Flux line */}
                                    <path
                                        d={fluxPath}
                                        fill="none"
                                        stroke="#06b6d4"
                                        strokeWidth="2"
                                        className="transition-all duration-200"
                                    />

                                    {/* Flux area fill */}
                                    <path
                                        d={fluxPath + ` L ${(fluxData.length - 1) * 20} 100 L 0 100 Z`}
                                        fill="url(#fluxGradient)"
                                        className="transition-all duration-200"
                                    />
                                </svg>
                            </div>
                        </div>

                        {/* CTA Button */}
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center justify-center space-x-2 px-8 py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 rounded-xl font-medium text-white transition-all"
                        >
                            <span>View Dashboard</span>
                            <ExternalLink className="w-4 h-4" />
                        </Link>

                        {/* Disclaimer */}
                        <p className="text-xs text-gray-600 mt-4 italic">
                            This is an automated alert. System credentials required for access.
                        </p>
                    </div>

                    {/* Footer Links */}
                    <div className="border-t border-[#2a2a3a] p-4 flex items-center justify-between">
                        <div className="flex items-center space-x-6 text-sm text-gray-500">
                            <Link href="/dashboard/alerts" className="hover:text-white transition-colors">
                                Alert Settings
                            </Link>
                            <Link href="/docs" className="hover:text-white transition-colors">
                                Developer API Docs
                            </Link>
                        </div>
                        <div className="flex items-center space-x-3">
                            <a href="#" className="p-2 hover:bg-[#1a1a24] rounded-lg transition-colors">
                                <Linkedin className="w-4 h-4 text-gray-500" />
                            </a>
                            <a href="#" className="p-2 hover:bg-[#1a1a24] rounded-lg transition-colors">
                                <HelpCircle className="w-4 h-4 text-gray-500" />
                            </a>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center mt-6 text-sm text-gray-600">
                    © 2024 ZERO-COMP SOLAR MONITORING SYSTEMS | DATA STREAM VIA GOES-16
                </div>
            </div>
        </div>
    )
}
