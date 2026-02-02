'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutGrid,
    Radio,
    Code2,
    Bell,
    Settings,
    ChevronRight
} from 'lucide-react'

interface SidebarProps {
    alertCount?: number
}

const navItems = [
    {
        section: 'MONITORING',
        items: [
            { name: 'Overview', href: '/dashboard', icon: LayoutGrid },
            { name: 'Live Feed', href: '/dashboard/feed', icon: Radio },
            { name: 'API Explorer', href: '/dashboard/api', icon: Code2 },
        ]
    },
    {
        section: 'MANAGEMENT',
        items: [
            { name: 'Alerts', href: '/dashboard/alerts', icon: Bell, badge: true },
            { name: 'Settings', href: '/dashboard/settings', icon: Settings },
        ]
    }
]

export default function Sidebar({ alertCount = 2 }: SidebarProps) {
    const pathname = usePathname()

    return (
        <aside className="w-56 h-screen bg-[#0a0a0f] border-r border-[#1a1a24] flex flex-col fixed left-0 top-0">
            {/* Logo */}
            <div className="p-4 border-b border-[#1a1a24]">
                <Link href="/dashboard" className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">Z</span>
                    </div>
                    <span className="text-white font-semibold">ZERO-COMP</span>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
                {navItems.map((section) => (
                    <div key={section.section}>
                        <h3 className="text-[10px] font-medium text-gray-600 uppercase tracking-wider mb-3">
                            {section.section}
                        </h3>
                        <ul className="space-y-1">
                            {section.items.map((item) => {
                                const isActive = pathname === item.href ||
                                    (item.href !== '/dashboard' && pathname?.startsWith(item.href))
                                const Icon = item.icon

                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${isActive
                                                    ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                                                    : 'text-gray-400 hover:text-white hover:bg-[#12121a]'
                                                }`}
                                        >
                                            <div className="flex items-center space-x-3">
                                                <Icon className="w-4 h-4" />
                                                <span>{item.name}</span>
                                            </div>
                                            {item.badge && alertCount > 0 && (
                                                <span className="px-2 py-0.5 text-xs bg-red-500 text-white rounded-full">
                                                    {alertCount}
                                                </span>
                                            )}
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            {/* System Status */}
            <div className="p-4 border-t border-[#1a1a24]">
                <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs text-gray-500">SYSTEM NOMINAL</span>
                </div>
                <div className="mt-2 h-1 bg-[#1a1a24] rounded-full overflow-hidden">
                    <div className="h-full w-3/4 bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full" />
                </div>
            </div>
        </aside>
    )
}
