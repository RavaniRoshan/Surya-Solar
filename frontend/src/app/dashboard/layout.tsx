'use client'

import { useAuth } from '@/contexts/AuthContext'
import Sidebar from '@/components/dashboard/Sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  useAuth()

  return (
    <div className="min-h-screen bg-[#0B1120]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="ml-56">
        {/* Top Bar */}
        <header className="h-16 bg-[#0B1120] border-b border-gray-800/50 flex items-center justify-between px-8 sticky top-0 z-40">
          {/* Title */}
          <div>
            <h1 className="text-2xl font-bold text-white">Mission Control</h1>
            <p className="text-xs text-gray-500 uppercase tracking-wider">SOLAR FLARE MONITORING SYSTEM</p>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-6">
            {/* Solar Status */}
            <div className="flex items-center space-x-4 px-4 py-2 bg-gray-800/30 rounded-xl border border-gray-700/50">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-emerald-400 text-sm font-medium">Normal Activity</span>
              </div>
              <div className="w-px h-4 bg-gray-700" />
              <span className="text-gray-400 text-sm">Solar Status</span>
            </div>

            {/* Time */}
            <div className="text-right">
              <div className="text-xl font-mono text-white font-bold">
                {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })} UTC
              </div>
              <div className="text-xs text-gray-500 uppercase">SYSTEM SYNCHRONIZED</div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="px-8 py-4 border-t border-gray-800/50 flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-8">
            <span>ENCRYPTION: AES-256</span>
            <span>UPTIME: 99.998%</span>
            <span>NODE: US-EAST-CORE</span>
          </div>
          <span>© 2024 ZERO-COMP AEROSPACE</span>
        </footer>
      </div>
    </div>
  )
}