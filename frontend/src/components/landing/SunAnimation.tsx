'use client'

import { motion } from 'framer-motion'

export function SunAnimation() {
    // Pre-calculate rays to avoid hydration mismatch
    const rays = Array.from({ length: 12 }).map((_, i) => ({
        rotation: i * 30,
        delay: i * 0.1
    }))

    return (
        <div className="relative w-64 h-64 flex items-center justify-center">
            {/* Glow Effect */}
            <motion.div
                className="absolute inset-0 bg-orange-400/20 rounded-full blur-3xl"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 4, repeat: Infinity }}
            />

            <svg viewBox="0 0 200 200" className="w-full h-full relative z-10">
                <defs>
                    <radialGradient id="sunGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="0%" stopColor="#FEF3C7" />
                        <stop offset="70%" stopColor="#FBBF24" />
                        <stop offset="100%" stopColor="#F59E0B" />
                    </radialGradient>
                </defs>

                {/* Rays */}
                <g transform="translate(100, 100)">
                    {rays.map((ray, i) => (
                        <motion.line
                            key={i}
                            x1="0"
                            y1="-50"
                            x2="0"
                            y2="-90"
                            stroke="#FCD34D"
                            strokeWidth="3"
                            transform={`rotate(${ray.rotation})`}
                            strokeLinecap="round"
                            initial={{ opacity: 0.6 }}
                            animate={{ opacity: [0.4, 0.8, 0.4], height: ["40px", "50px", "40px"] }}
                            transition={{
                                duration: 2,
                                repeat: Infinity,
                                delay: ray.delay,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </g>

                {/* Sun Body with 3D feel */}
                <motion.circle
                    cx="100"
                    cy="100"
                    r="45"
                    fill="url(#sunGradient)"
                    whileHover={{ scale: 1.1 }}
                    transition={{ type: "spring", stiffness: 300 }}
                />

                {/* Inner Highlight for 3D effect */}
                <circle cx="85" cy="85" r="15" fill="white" opacity="0.3" />
            </svg>
        </div>
    )
}
