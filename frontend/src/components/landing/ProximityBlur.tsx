'use client'

import React, { useRef, useState } from 'react'
import Link from 'next/link'

export function ProximityBlur() {
    const textRef = useRef<HTMLDivElement>(null)
    const [isHovered, setIsHovered] = useState(false)

    const handleMouseEnter = () => {
        setIsHovered(true)
    }

    const handleMouseLeave = () => {
        setIsHovered(false)
    }

    return (
        <div className="w-full py-32 bg-black flex items-center justify-center overflow-hidden">
            <Link href="/dashboard">
                <div
                    ref={textRef}
                    className="relative cursor-pointer"
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    {/* Background glow effect */}
                    <div 
                        className={`absolute inset-0 bg-gradient-to-r from-orange-500/20 via-amber-500/20 to-orange-500/20 blur-3xl transition-opacity duration-700 ${
                            isHovered ? 'opacity-100' : 'opacity-0'
                        }`}
                    />
                    
                    <h2
                        className={`text-7xl md:text-9xl font-sans font-bold tracking-tighter transition-all duration-500 ease-out relative ${
                            isHovered 
                                ? 'text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-amber-500 to-orange-400 scale-105' 
                                : 'text-white'
                        }`}
                        style={{
                            filter: isHovered ? 'blur(0px)' : 'blur(0px)',
                        }}
                    >
                        {/* Show text that transitions smoothly */}
                        <span 
                            className={`absolute inset-0 flex items-center justify-center transition-all duration-500 ${
                                isHovered ? 'opacity-0 blur-sm' : 'opacity-100 blur-0'
                            }`}
                        >
                            ZERO-COMP
                        </span>
                        <span 
                            className={`transition-all duration-500 ${
                                isHovered ? 'opacity-100 blur-0' : 'opacity-0 blur-sm'
                            }`}
                        >
                            ENTER SYSTEM
                        </span>
                    </h2>
                </div>
            </Link>
        </div>
    )
}
