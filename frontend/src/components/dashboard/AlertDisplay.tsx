'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle, Shield, Zap } from 'lucide-react'
import { CurrentAlertResponse } from '@/types/dashboard'
import { api } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/useWebSocket'
import { getNotificationManager } from '@/lib/notifications'

interface AlertDisplayProps {
  className?: string
}

const severityConfig = {
  low: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    icon: Shield,
    label: 'Low Risk',
    description: 'Normal solar activity'
  },
  medium: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    icon: AlertTriangle,
    label: 'Medium Risk',
    description: 'Elevated solar activity'
  },
  high: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    icon: Zap,
    label: 'High Risk',
    description: 'Dangerous solar activity'
  }
}

export default function AlertDisplay({ className = '' }: AlertDisplayProps) {
  const [currentAlert, setCurrentAlert] = useState<CurrentAlertResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const notificationManager = getNotificationManager()

  const { isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'alert' && message.data) {
        // Update current alert with real-time data
        const alertData = message.data
        setCurrentAlert(alertData)
        setLastUpdate(new Date())
        setError(null)
        
        // Show notification for medium/high severity alerts
        if (alertData.severity_level === 'medium' || alertData.severity_level === 'high') {
          notificationManager.showAlertNotification({
            severity: alertData.severity_level,
            probability: alertData.current_probability,
            timestamp: alertData.last_updated,
            message: alertData.alert_active ? 'Solar flare alert is active!' : undefined
          })
        }
      }
    }
  })

  const fetchCurrentAlert = async () => {
    try {
      setLoading(true)
      const response = await api.alerts.getCurrent()
      setCurrentAlert(response.data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      console.error('Failed to fetch current alert:', err)
      setError('Failed to load current alert data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCurrentAlert()
    
    // Request notification permission on component mount
    notificationManager.requestPermission()
    
    // Fallback polling if WebSocket is not connected
    let interval: NodeJS.Timeout | null = null
    
    if (!isConnected) {
      interval = setInterval(fetchCurrentAlert, 30000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isConnected])

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-red-600 text-center">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
          <p>{error}</p>
          <button 
            onClick={fetchCurrentAlert}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!currentAlert) {
    return null
  }

  const config = severityConfig[currentAlert.severity_level]
  const IconComponent = config.icon
  const probabilityPercentage = (currentAlert.current_probability * 100).toFixed(1)

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Current Solar Weather</h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.color} ${config.borderColor} border`}>
          {currentAlert.alert_active ? 'ALERT ACTIVE' : 'MONITORING'}
        </div>
      </div>

      <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 mb-4`}>
        <div className="flex items-center mb-3">
          <IconComponent className={`h-6 w-6 ${config.color} mr-3`} />
          <div>
            <h3 className={`font-semibold ${config.color}`}>{config.label}</h3>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Flare Probability</p>
            <p className={`text-2xl font-bold ${config.color}`}>{probabilityPercentage}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Severity Level</p>
            <p className={`text-lg font-semibold ${config.color} capitalize`}>
              {currentAlert.severity_level}
            </p>
          </div>
        </div>
      </div>

      <div className="text-sm text-gray-500 space-y-1">
        <div className="flex items-center justify-between">
          <p>Last Updated: {new Date(currentAlert.last_updated).toLocaleString()}</p>
          {isConnected && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Live
            </span>
          )}
        </div>
        <p>Next Update: {new Date(currentAlert.next_update).toLocaleString()}</p>
        {lastUpdate && (
          <p className="text-xs">
            Data received: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  )
}