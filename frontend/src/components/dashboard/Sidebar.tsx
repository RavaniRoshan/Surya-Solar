'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutGrid,
    Bell,
    Database,
    Code2,
    Settings,
    LogOut
} from 'lucide-react'

const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutGrid },
    { name: 'Live Alerts', href: '/dashboard/alerts', icon: Bell },
    { name: 'Historical Data', href: '/dashboard/historical', icon: Database },
    { name: 'API Management', href: '/dashboard/api', icon: Code2 },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function Sidebar() {
    const pathname = usePathname()

    return (
        <aside className="w-56 h-screen bg-[#0B1120] border-r border-gray-800/50 flex flex-col fixed left-0 top-0">
            {/* Logo */}
            <div className="p-5 border-b border-gray-800/50">
                <Link href="/dashboard" className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <span className="text-white font-bold text-lg">✦</span>
                    </div>
                    <span className="text-white font-bold tracking-tight">ZERO-COMP</span>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== '/dashboard' && pathname?.startsWith(item.href))
                    const Icon = item.icon

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive
                                    ? 'bg-blue-500/20 text-blue-400 border-l-2 border-blue-400'
                                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                                }`}
                        >
                            <Icon className="w-5 h-5" />
                            <span>{item.name}</span>
                        </Link>
                    )
                })}
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-gray-800/50">
                <div className="flex items-center space-x-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        JD
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white truncate">John Doe</div>
                        <div className="text-xs text-gray-500">Enterprise Admin</div>
                    </div>
                </div>
                <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/50 transition-colors text-sm">
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>
    )
}
