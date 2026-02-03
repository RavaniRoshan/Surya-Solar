'use client'

import { useRef } from 'react'
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion'
import { Activity, Wind, Zap } from 'lucide-react'

interface HeroCardProps {
    isDark?: boolean
}

export function HeroCard({ isDark = false }: HeroCardProps) {
    const ref = useRef<HTMLDivElement>(null)

    const x = useMotionValue(0)
    const y = useMotionValue(0)

    // Smooth spring physics for the tilt
    const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [10, -10]), { stiffness: 150, damping: 20 })
    const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-10, 10]), { stiffness: 150, damping: 20 })

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return
        const rect = ref.current.getBoundingClientRect()

        // Normalize coordinates -0.5 to 0.5
        const width = rect.width
        const height = rect.height

        const mouseX = e.clientX - rect.left
        const mouseY = e.clientY - rect.top

        const xPct = mouseX / width - 0.5
        const yPct = mouseY / height - 0.5

        x.set(xPct)
        y.set(yPct)
    }

    const handleMouseLeave = () => {
        x.set(0)
        y.set(0)
    }

    return (
        <motion.div
            ref={ref}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            style={{
                rotateX,
                rotateY,
                transformStyle: "preserve-3d"
            }}
            className="relative w-full max-w-4xl mx-auto perspective-1000"
        >
            <div className={`rounded-3xl border shadow-2xl overflow-hidden p-6 md:p-8 ${isDark
                    ? 'bg-gray-900 border-gray-700'
                    : 'bg-white border-gray-100'
                }`}>
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Solar Activity Overview</h3>
                        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Live Telemetry from SDO-1</p>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${isDark ? 'text-green-400 bg-green-900/50' : 'text-green-600 bg-green-50'
                            }`}>SYSTEM NORMAL</span>
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Main Chart Area */}
                    <div className={`rounded-2xl p-6 min-h-[220px] relative overflow-hidden group ${isDark ? 'bg-gray-800' : 'bg-gray-50'
                        }`}>
                        {/* Animated Chart Line */}
                        <svg viewBox="0 0 300 150" className="w-full h-full absolute inset-0 text-purple-500">
                            <motion.path
                                d="M0,100 C50,100 50,50 100,50 C150,50 150,120 200,80 C250,40 250,90 300,60 L300,150 L0,150 Z"
                                fill={isDark ? "rgba(147, 51, 234, 0.2)" : "rgba(147, 51, 234, 0.1)"}
                            />
                            <motion.path
                                d="M0,100 C50,100 50,50 100,50 C150,50 150,120 200,80 C250,40 250,90 300,60"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="3"
                                initial={{ pathLength: 0 }}
                                animate={{ pathLength: 1 }}
                                transition={{ duration: 2, ease: "easeInOut" }}
                            />
                        </svg>

                        {/* Floating details on hover */}
                        <motion.div
                            className={`absolute top-1/2 left-1/2 px-4 py-2 rounded-lg shadow-lg border ${isDark
                                    ? 'bg-gray-900 border-purple-500/30'
                                    : 'bg-white border-purple-100'
                                }`}
                            style={{ x: "-50%", y: "-50%", translateZ: 50 }}
                        >
                            <div className={`text-xs uppercase ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Current Peak</div>
                            <div className="text-2xl font-bold text-purple-500">X-1.4</div>
                        </motion.div>
                    </div>

                    {/* Stats Grid with Floating Cards */}
                    <div className="space-y-4">
                        <motion.div
                            className={`p-4 rounded-xl border shadow-sm flex items-center justify-between ${isDark
                                    ? 'bg-gray-800 border-gray-700'
                                    : 'bg-white border-gray-100'
                                }`}
                            whileHover={{ scale: 1.05, translateZ: 20 }}
                        >
                            <div className="flex items-center space-x-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-orange-900/50' : 'bg-orange-100'
                                    }`}>
                                    <Activity className={`w-5 h-5 ${isDark ? 'text-orange-400' : 'text-orange-600'}`} />
                                </div>
                                <div>
                                    <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Flare Probability</div>
                                    <div className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>87%</div>
                                </div>
                            </div>
                            <div className={`h-10 w-16 rounded-md flex items-end p-1 space-x-1 ${isDark ? 'bg-orange-900/30' : 'bg-orange-50'
                                }`}>
                                <div className="w-1/3 bg-orange-400 h-[60%] rounded-sm"></div>
                                <div className="w-1/3 bg-orange-400 h-[40%] rounded-sm"></div>
                                <div className="w-1/3 bg-orange-400 h-[80%] rounded-sm"></div>
                            </div>
                        </motion.div>

                        <motion.div
                            className={`p-4 rounded-xl border shadow-sm flex items-center justify-between ${isDark
                                    ? 'bg-gray-800 border-gray-700'
                                    : 'bg-white border-gray-100'
                                }`}
                            whileHover={{ scale: 1.05, translateZ: 20 }}
                        >
                            <div className="flex items-center space-x-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-blue-900/50' : 'bg-blue-100'
                                    }`}>
                                    <Wind className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                                </div>
                                <div>
                                    <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Solar Wind</div>
                                    <div className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>450 km/s</div>
                                </div>
                            </div>
                            <div className={`text-xs font-semibold px-2 py-1 rounded text-center min-w-[60px] ${isDark ? 'text-blue-400 bg-blue-900/50' : 'text-blue-600 bg-blue-50'
                                }`}>
                                FAST
                            </div>
                        </motion.div>

                        <motion.div
                            className={`p-4 rounded-xl border shadow-sm flex items-center justify-between ${isDark
                                    ? 'bg-gray-800 border-gray-700'
                                    : 'bg-white border-gray-100'
                                }`}
                            whileHover={{ scale: 1.05, translateZ: 20 }}
                        >
                            <div className="flex items-center space-x-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? 'bg-purple-900/50' : 'bg-purple-100'
                                    }`}>
                                    <Zap className={`w-5 h-5 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                                </div>
                                <div>
                                    <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>KP Index</div>
                                    <div className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>7.33</div>
                                </div>
                            </div>
                            <div className={`relative w-16 h-1 rounded-full ${isDark ? 'bg-gray-700' : 'bg-gray-100'}`}>
                                <div className="absolute top-0 left-0 h-full w-[70%] bg-purple-500 rounded-full"></div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>

            {/* Decorative Glow */}
            <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] blur-[100px] -z-10 pointer-events-none ${isDark ? 'bg-purple-600/20' : 'bg-purple-500/10'
                }`} />
        </motion.div>
    )
}
