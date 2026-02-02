'use client'

import { useAuth } from '@/contexts/AuthContext'
import Sidebar from '@/components/dashboard/Sidebar'
import { Search, User } from 'lucide-react'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="ml-56">
        {/* Top Bar */}
        <header className="h-14 bg-[#0a0a0f] border-b border-[#1a1a24] flex items-center justify-between px-6 sticky top-0 z-40">
          {/* Status Indicators */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-[#12121a] rounded-lg border border-[#2a2a3a]">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-xs text-gray-400">Status: <span className="text-emerald-400">Quiet</span></span>
            </div>
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-[#12121a] rounded-lg border border-[#2a2a3a]">
              <span className="text-xs text-gray-400">K-Index: <span className="text-purple-400">2</span></span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
              <span>L1 Node Active: 149.6M km</span>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-500 hover:text-white transition-colors">
              <Search className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm text-white font-medium">
                  {user?.email?.split('@')[0] || 'User'}
                </p>
                <p className="text-xs text-gray-500">SYSTEM ADMIN</p>
              </div>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}