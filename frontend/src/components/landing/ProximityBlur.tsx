'use client'

import React, { useRef, useEffect, useState } from 'react'

export function ProximityBlur() {
    const textRef = useRef<HTMLDivElement>(null)
    const [isHovered, setIsHovered] = useState(false)
    const requestRef = useRef<number>(null)

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!textRef.current) return

            const rect = textRef.current.getBoundingClientRect()
            const centerX = rect.left + rect.width / 2
            const centerY = rect.top + rect.height / 2

            const distance = Math.sqrt(
                Math.pow(e.clientX - centerX, 2) +
                Math.pow(e.clientY - centerY, 2)
            )

            // Calculate blur: 0px at 0 distance, 20px at > 400px distance
            const maxDistance = 400
            const maxBlur = 20

            let blurAmount = 0
            if (distance < maxDistance) {
                blurAmount = (distance / maxDistance) * maxBlur
            } else {
                blurAmount = maxBlur
            }

            // Apply blur directly to style for performance
            if (textRef.current && !textRef.current.dataset.hovered) {
                textRef.current.style.filter = `blur(${blurAmount}px)`
                textRef.current.style.opacity = Math.max(0.2, 1 - (blurAmount / maxBlur) * 0.5).toString()
            }
        }

        const loop = () => {
            // We can use this for smoother interpolation if needed, 
            // but direct mouse mapping is usually responsive enough for this effect.
            // For now, attaching directly to mousemove is efficient enough if we don't do heavy calc.
        }

        window.addEventListener('mousemove', handleMouseMove)
        return () => {
            window.removeEventListener('mousemove', handleMouseMove)
        }
    }, [])

    const handleMouseEnter = () => {
        setIsHovered(true)
        if (textRef.current) {
            textRef.current.dataset.hovered = "true"
            textRef.current.style.filter = 'blur(0px)'
            textRef.current.style.opacity = '1'
        }
    }

    const handleMouseLeave = () => {
        setIsHovered(false)
        if (textRef.current) {
            delete textRef.current.dataset.hovered
        }
    }

    return (
        <div className="w-full py-32 bg-black flex items-center justify-center overflow-hidden">
            <div
                ref={textRef}
                className="relative cursor-pointer transition-colors duration-300"
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
            >
                <h2
                    className={`text-8xl md:text-9xl font-sans font-bold tracking-tighter transition-all duration-300 ${isHovered ? 'text-purple-500 scale-105' : 'text-white'
                        }`}
                >
                    {isHovered ? 'ENTER SYSTEM' : 'ZERO-COMP'}
                </h2>
            </div>
        </div>
    )
}
