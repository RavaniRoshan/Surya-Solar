'use client'

import { motion } from 'framer-motion'
import { Globe, Zap, Satellite, Database, Cloud } from 'lucide-react'

const integrations = [
    {
        icon: Satellite,
        name: "NASA Data Pipeline",
        desc: "Direct SDO ingest",
        lightColor: "bg-orange-100 text-orange-600",
        darkColor: "bg-orange-900/50 text-orange-400"
    },
    {
        icon: Globe,
        name: "AWS Cloud Ready",
        desc: "Deploy to Lambda",
        lightColor: "bg-amber-100 text-amber-600",
        darkColor: "bg-amber-900/50 text-amber-400"
    },
    {
        icon: Zap,
        name: "Simplified Nav",
        desc: "Real-time API",
        lightColor: "bg-blue-100 text-blue-600",
        darkColor: "bg-blue-900/50 text-blue-400"
    },
    {
        icon: Database,
        name: "Postgres Sync",
        desc: "Auto-archiving",
        lightColor: "bg-purple-100 text-purple-600",
        darkColor: "bg-purple-900/50 text-purple-400"
    },
    {
        icon: Cloud,
        name: "Google Cloud",
        desc: "BigQuery native",
        lightColor: "bg-red-100 text-red-600",
        darkColor: "bg-red-900/50 text-red-400"
    }
]

interface IntegrationsProps {
    isDark?: boolean
}

export function Integrations({ isDark = false }: IntegrationsProps) {
    return (
        <div className="w-full overflow-hidden py-10 relative">
            <div className={`absolute inset-y-0 left-0 w-32 z-10 bg-gradient-to-r ${isDark ? 'from-[#0A0A0F] to-transparent' : 'from-gray-50 to-transparent'
                }`} />
            <div className={`absolute inset-y-0 right-0 w-32 z-10 bg-gradient-to-l ${isDark ? 'from-[#0A0A0F] to-transparent' : 'from-gray-50 to-transparent'
                }`} />

            <motion.div
                className="flex space-x-6 w-max"
                animate={{ x: ["0%", "-50%"] }}
                transition={{
                    duration: 30,
                    ease: "linear",
                    repeat: Infinity
                }}
                whileHover={{ animationPlayState: "paused" }}
            >
                {/* Double the list for seamless loop */}
                {[...integrations, ...integrations, ...integrations].map((item, i) => (
                    <motion.div
                        key={i}
                        className={`w-80 rounded-2xl border p-6 flex items-start space-x-4 transition-shadow cursor-pointer ${isDark
                                ? 'bg-gray-900 border-gray-700 hover:shadow-xl hover:shadow-purple-500/10'
                                : 'bg-white border-gray-100 hover:shadow-lg'
                            }`}
                        whileHover={{ scale: 1.02 }}
                    >
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${isDark ? item.darkColor : item.lightColor
                            }`}>
                            <item.icon className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</h3>
                            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{item.desc}</p>
                        </div>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    )
}
