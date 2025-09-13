'use client'

import { useAuth } from '@/contexts/AuthContext'
import AlertDisplay from '@/components/dashboard/AlertDisplay'
import HistoricalChart from '@/components/dashboard/HistoricalChart'
import AlertThresholds from '@/components/dashboard/AlertThresholds'
import SubscriptionManager from '@/components/dashboard/SubscriptionManager'
import ConnectionStatus from '@/components/dashboard/ConnectionStatus'
import { useWebSocket } from '@/hooks/useWebSocket'
import { getNotificationManager } from '@/lib/notifications'
import { useEffect } from 'react'

export const dynamic = 'force-dynamic'

export default function DashboardPage() {
  const { user } = useAuth()
  const notificationManager = getNotificationManager()
  
  const { connectionStatus, connect } = useWebSocket({
    onConnectionChange: (status) => {
      // Show connection notifications
      if (status.connected && !status.reconnecting) {
        notificationManager.showConnectionNotification(true)
      } else if (!status.connected && status.error) {
        notificationManager.showConnectionNotification(false, status.error)
      }
    }
  })

  useEffect(() => {
    // Request notification permission when dashboard loads
    notificationManager.requestPermission()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ZERO-COMP Dashboard</h1>
              <p className="text-gray-600">Solar Weather Prediction System</p>
            </div>
            <div className="flex items-center space-x-4">
              <ConnectionStatus 
                status={connectionStatus}
                onReconnect={connect}
              />
              <div className="text-right">
                <p className="text-sm text-gray-600">Welcome back,</p>
                <p className="font-medium text-gray-900">{user?.email}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Top Row - Current Alert and Quick Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AlertDisplay />
            </div>
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-md p-6 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">System Status</span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Operational
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Last Update</span>
                    <span className="text-sm font-medium text-gray-900">
                      {new Date().toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Model Version</span>
                    <span className="text-sm font-medium text-gray-900">Surya-1.0</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Data Source</span>
                    <span className="text-sm font-medium text-gray-900">NASA</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Historical Chart */}
          <div>
            <HistoricalChart />
          </div>

          {/* Bottom Row - Configuration and Subscription */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <AlertThresholds />
            </div>
            <div>
              <SubscriptionManager />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center">
            <div className="text-sm text-gray-600">
              © 2024 ZERO-COMP. Powered by NASA-IBM Surya-1.0
            </div>
            <div className="flex space-x-6 mt-4 sm:mt-0">
              <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Documentation</a>
              <a href="#" className="text-sm text-gray-600 hover:text-gray-900">API Reference</a>
              <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}