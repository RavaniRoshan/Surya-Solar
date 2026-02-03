'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Moon, Sun } from 'lucide-react'

interface NavbarProps {
    isDark?: boolean
    onThemeToggle?: () => void
}

export function Navbar({ isDark = false, onThemeToggle }: NavbarProps) {
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null)

    return (
        <nav className="fixed top-6 left-1/2 -translate-x-1/2 w-[95%] max-w-5xl z-50">
            <div className={`backdrop-blur-xl border shadow-lg rounded-2xl px-6 py-4 ${isDark
                    ? 'bg-gray-900/70 border-gray-700/50'
                    : 'bg-white/70 border-white/20'
                }`}>
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center space-x-2">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isDark ? 'bg-white' : 'bg-gray-900'
                            }`}>
                            <span className={`font-bold text-sm ${isDark ? 'text-gray-900' : 'text-white'}`}>Z</span>
                        </div>
                        <span className={`font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>ZERO-COMP</span>
                    </div>

                    {/* Desktop Nav */}
                    <div className="hidden md:flex items-center space-x-8">
                        {/* Platform Dropdown */}
                        <div
                            className="relative"
                            onMouseEnter={() => setActiveDropdown('platform')}
                            onMouseLeave={() => setActiveDropdown(null)}
                        >
                            <button className={`flex items-center space-x-1 text-sm font-medium transition-colors py-2 ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                                }`}>
                                <span>Platform</span>
                                <ChevronDown className="w-4 h-4" />
                            </button>

                            <AnimatePresence>
                                {activeDropdown === 'platform' && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className={`absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 rounded-xl shadow-xl border p-4 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'
                                            }`}
                                    >
                                        <div className="space-y-4">
                                            <div className="group cursor-pointer">
                                                <div className={`text-sm font-semibold transition-colors ${isDark ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                                                    }`}>Grid Protection</div>
                                                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>For power distributors</div>
                                            </div>
                                            <div className="group cursor-pointer">
                                                <div className={`text-sm font-semibold transition-colors ${isDark ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                                                    }`}>Satellite Ops</div>
                                                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Low latency telemetry</div>
                                            </div>
                                            <div className="group cursor-pointer">
                                                <div className={`text-sm font-semibold transition-colors ${isDark ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                                                    }`}>Aviation Safety</div>
                                                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Route planning tools</div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Solutions Dropdown */}
                        <div
                            className="relative"
                            onMouseEnter={() => setActiveDropdown('solutions')}
                            onMouseLeave={() => setActiveDropdown(null)}
                        >
                            <button className={`flex items-center space-x-1 text-sm font-medium transition-colors py-2 ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                                }`}>
                                <span>Solutions</span>
                                <ChevronDown className="w-4 h-4" />
                            </button>

                            <AnimatePresence>
                                {activeDropdown === 'solutions' && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className={`absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 rounded-xl shadow-xl border p-4 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-100'
                                            }`}
                                    >
                                        <div className="space-y-4">
                                            <div className="group cursor-pointer">
                                                <div className={`text-sm font-semibold transition-colors ${isDark ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                                                    }`}>Developer API</div>
                                                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>REST & GraphQL docs</div>
                                            </div>
                                            <div className="group cursor-pointer">
                                                <div className={`text-sm font-semibold transition-colors ${isDark ? 'text-white group-hover:text-purple-400' : 'text-gray-900 group-hover:text-purple-600'
                                                    }`}>Enterprise</div>
                                                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Custom SLAs & Support</div>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        <Link href="/pricing" className={`text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                            }`}>
                            Pricing
                        </Link>
                        <Link href="/docs" className={`text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                            }`}>
                            Docs
                        </Link>
                    </div>

                    {/* CTA & Theme Toggle */}
                    <div className="flex items-center space-x-4">
                        {/* Theme Toggle */}
                        {onThemeToggle && (
                            <button
                                onClick={onThemeToggle}
                                className={`p-2 rounded-lg transition-colors ${isDark
                                        ? 'text-gray-400 hover:text-white hover:bg-gray-800'
                                        : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                                    }`}
                                aria-label="Toggle theme"
                            >
                                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            </button>
                        )}

                        <Link href="/auth/login" className={`hidden sm:block text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                            }`}>
                            Log in
                        </Link>
                        <Link
                            href="/auth/signup"
                            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all hover:scale-105 ${isDark
                                    ? 'bg-white hover:bg-gray-100 text-gray-900'
                                    : 'bg-gray-900 hover:bg-gray-800 text-white'
                                }`}
                        >
                            Get started
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    )
}
