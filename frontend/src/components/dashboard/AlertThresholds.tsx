'use client'

import { useState, useEffect } from 'react'
import { Settings, Save, RotateCcw } from 'lucide-react'
import { UserSubscription } from '@/types/dashboard'
import { api } from '@/lib/api-client'

interface AlertThresholdsProps {
  className?: string
}

interface ThresholdSettings {
  low: number
  medium: number
  high: number
}

export default function AlertThresholds({ className = '' }: AlertThresholdsProps) {
  const [subscription, setSubscription] = useState<UserSubscription | null>(null)
  const [thresholds, setThresholds] = useState<ThresholdSettings>({
    low: 25,
    medium: 50,
    high: 75
  })
  const [originalThresholds, setOriginalThresholds] = useState<ThresholdSettings>({
    low: 25,
    medium: 50,
    high: 75
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const fetchSubscription = async () => {
    try {
      setLoading(true)
      const response = await api.users.getSubscription()
      const sub: UserSubscription = response.data
      setSubscription(sub)
      
      if (sub.alert_thresholds) {
        const newThresholds = {
          low: sub.alert_thresholds.low * 100, // Convert from decimal to percentage
          medium: sub.alert_thresholds.medium * 100,
          high: sub.alert_thresholds.high * 100
        }
        setThresholds(newThresholds)
        setOriginalThresholds(newThresholds)
      }
      setError(null)
    } catch (err) {
      console.error('Failed to fetch subscription:', err)
      setError('Failed to load subscription data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubscription()
  }, [])

  const handleThresholdChange = (level: keyof ThresholdSettings, value: string) => {
    const numValue = parseFloat(value)
    if (isNaN(numValue) || numValue < 0 || numValue > 100) return
    
    setThresholds(prev => ({
      ...prev,
      [level]: numValue
    }))
    setSuccess(false)
  }

  const validateThresholds = (): string | null => {
    if (thresholds.low >= thresholds.medium) {
      return 'Low threshold must be less than medium threshold'
    }
    if (thresholds.medium >= thresholds.high) {
      return 'Medium threshold must be less than high threshold'
    }
    if (thresholds.high > 100) {
      return 'High threshold cannot exceed 100%'
    }
    return null
  }

  const saveThresholds = async () => {
    const validationError = validateThresholds()
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      await api.users.updateSubscription({
        alert_thresholds: {
          low: thresholds.low / 100, // Convert back to decimal
          medium: thresholds.medium / 100,
          high: thresholds.high / 100
        }
      })
      
      setOriginalThresholds(thresholds)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      console.error('Failed to save thresholds:', err)
      setError('Failed to save threshold settings')
    } finally {
      setSaving(false)
    }
  }

  const resetThresholds = () => {
    setThresholds(originalThresholds)
    setError(null)
    setSuccess(false)
  }

  const hasChanges = JSON.stringify(thresholds) !== JSON.stringify(originalThresholds)

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  // Check if user has access to threshold configuration
  const canConfigureThresholds = subscription?.tier !== 'free'

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center mb-6">
        <Settings className="h-5 w-5 text-gray-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">Alert Thresholds</h2>
      </div>

      {!canConfigureThresholds ? (
        <div className="text-center py-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 font-medium mb-2">Upgrade Required</p>
            <p className="text-yellow-700 text-sm">
              Alert threshold configuration is available for Pro and Enterprise subscribers only.
            </p>
          </div>
        </div>
      ) : (
        <>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800 text-sm">Threshold settings saved successfully!</p>
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Low Risk Threshold
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={thresholds.low}
                  onChange={(e) => handleThresholdChange('low', e.target.value)}
                  className="block w-24 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-gray-600">%</span>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${thresholds.low}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Alerts below this threshold are considered low risk
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Medium Risk Threshold
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={thresholds.medium}
                  onChange={(e) => handleThresholdChange('medium', e.target.value)}
                  className="block w-24 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-gray-600">%</span>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${thresholds.medium}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Alerts above this threshold are considered medium risk
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                High Risk Threshold
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={thresholds.high}
                  onChange={(e) => handleThresholdChange('high', e.target.value)}
                  className="block w-24 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-gray-600">%</span>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${thresholds.high}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Alerts above this threshold are considered high risk
              </p>
            </div>
          </div>

          {hasChanges && (
            <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={resetThresholds}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </button>
              <button
                onClick={saveThresholds}
                disabled={saving}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}