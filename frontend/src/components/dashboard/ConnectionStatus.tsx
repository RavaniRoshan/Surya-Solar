'use client'

import { useState, useEffect } from 'react'
import { Wifi, WifiOff, RotateCcw, AlertCircle } from 'lucide-react'
import { ConnectionStatus as ConnectionStatusType } from '@/lib/websocket-client'

interface ConnectionStatusProps {
  status: ConnectionStatusType
  onReconnect?: () => void
  className?: string
}

export default function ConnectionStatus({ status, onReconnect, className = '' }: ConnectionStatusProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [lastConnectedText, setLastConnectedText] = useState<string>('')

  useEffect(() => {
    if (status.lastConnected) {
      const updateLastConnected = () => {
        const now = new Date()
        const diff = now.getTime() - status.lastConnected!.getTime()
        const minutes = Math.floor(diff / 60000)
        const seconds = Math.floor((diff % 60000) / 1000)
        
        if (minutes > 0) {
          setLastConnectedText(`${minutes}m ${seconds}s ago`)
        } else {
          setLastConnectedText(`${seconds}s ago`)
        }
      }

      updateLastConnected()
      const interval = setInterval(updateLastConnected, 1000)
      return () => clearInterval(interval)
    }
  }, [status.lastConnected])

  const getStatusConfig = () => {
    if (status.connected) {
      return {
        icon: Wifi,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        label: 'Connected',
        description: 'Real-time monitoring active'
      }
    } else if (status.reconnecting) {
      return {
        icon: RotateCcw,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        label: 'Reconnecting',
        description: `Attempt ${status.reconnectAttempts + 1}`
      }
    } else {
      return {
        icon: status.error ? AlertCircle : WifiOff,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        label: 'Disconnected',
        description: status.error || 'Real-time monitoring unavailable'
      }
    }
  }

  const config = getStatusConfig()
  const IconComponent = config.icon

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setShowDetails(!showDetails)}
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors ${config.bgColor} ${config.borderColor} hover:opacity-80`}
      >
        <IconComponent 
          className={`h-4 w-4 ${config.color} ${status.reconnecting ? 'animate-spin' : ''}`} 
        />
        <span className={`text-sm font-medium ${config.color}`}>
          {config.label}
        </span>
      </button>

      {showDetails && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Connection Status</h3>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`font-medium ${config.color}`}>
                  {config.label}
                </span>
              </div>
              
              {status.lastConnected && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Connected:</span>
                  <span className="text-gray-900">{lastConnectedText}</span>
                </div>
              )}
              
              {status.reconnectAttempts > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Reconnect Attempts:</span>
                  <span className="text-gray-900">{status.reconnectAttempts}</span>
                </div>
              )}
              
              {status.error && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                  <p className="text-red-700 text-xs">{status.error}</p>
                </div>
              )}
            </div>
            
            <div className="pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-600 mb-2">
                {config.description}
              </p>
              
              {!status.connected && onReconnect && (
                <button
                  onClick={() => {
                    onReconnect()
                    setShowDetails(false)
                  }}
                  disabled={status.reconnecting}
                  className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {status.reconnecting ? 'Reconnecting...' : 'Reconnect Now'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}