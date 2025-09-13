'use client'

import { useState, useEffect } from 'react'
import { CreditCard, Check, Zap, Crown, Key, Webhook, BarChart3 } from 'lucide-react'
import { UserSubscription, ApiUsage, SubscriptionTier } from '@/types/dashboard'
import { api } from '@/lib/api-client'

interface SubscriptionManagerProps {
  className?: string
}

const tierFeatures = {
  free: {
    name: 'Free',
    price: '$0',
    period: 'forever',
    icon: BarChart3,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    features: [
      'Web dashboard access',
      'Current alert viewing',
      'Basic historical data (24h)',
      'Community support'
    ],
    limits: {
      requests_per_hour: 10,
      websocket_connections: 0
    }
  },
  pro: {
    name: 'Pro',
    price: '$50',
    period: 'per month',
    icon: Zap,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    features: [
      'All Free features',
      'API access with authentication',
      'WebSocket real-time alerts',
      'Extended historical data (30 days)',
      'Custom alert thresholds',
      'Email support'
    ],
    limits: {
      requests_per_hour: 1000,
      websocket_connections: 5
    }
  },
  enterprise: {
    name: 'Enterprise',
    price: '$500',
    period: 'per month',
    icon: Crown,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    features: [
      'All Pro features',
      'Multi-endpoint dashboards',
      'SLA guarantees (99.9% uptime)',
      'CSV data exports',
      'Unlimited historical data',
      'Webhook notifications',
      'Priority support',
      'Custom integrations'
    ],
    limits: {
      requests_per_hour: 10000,
      websocket_connections: 50
    }
  }
}

export default function SubscriptionManager({ className = '' }: SubscriptionManagerProps) {
  const [subscription, setSubscription] = useState<UserSubscription | null>(null)
  const [apiUsage, setApiUsage] = useState<ApiUsage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatingApiKey, setGeneratingApiKey] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [subResponse, usageResponse] = await Promise.all([
        api.users.getSubscription(),
        api.users.getApiUsage()
      ])
      
      setSubscription(subResponse.data)
      setApiUsage(usageResponse.data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch subscription data:', err)
      setError('Failed to load subscription information')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const generateApiKey = async () => {
    try {
      setGeneratingApiKey(true)
      await api.users.generateApiKey()
      await fetchData() // Refresh data to get new API key
    } catch (err) {
      console.error('Failed to generate API key:', err)
      setError('Failed to generate API key')
    } finally {
      setGeneratingApiKey(false)
    }
  }

  const handleUpgrade = (tier: SubscriptionTier) => {
    // In a real implementation, this would redirect to Razorpay payment
    console.log(`Upgrading to ${tier}`)
    alert(`Upgrade to ${tier} - Payment integration would be implemented here`)
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-64 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-red-600 text-center">
          <CreditCard className="h-8 w-8 mx-auto mb-2" />
          <p>{error}</p>
          <button 
            onClick={fetchData}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const currentTier = subscription?.tier || 'free'
  const currentTierConfig = tierFeatures[currentTier]

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center mb-6">
        <CreditCard className="h-5 w-5 text-gray-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">Subscription Management</h2>
      </div>

      {/* Current Subscription Status */}
      <div className={`${currentTierConfig.bgColor} ${currentTierConfig.borderColor} border rounded-lg p-4 mb-6`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            <currentTierConfig.icon className={`h-6 w-6 ${currentTierConfig.color} mr-3`} />
            <div>
              <h3 className={`font-semibold ${currentTierConfig.color}`}>
                Current Plan: {currentTierConfig.name}
              </h3>
              <p className="text-sm text-gray-600">
                {currentTierConfig.price} {currentTierConfig.period}
              </p>
            </div>
          </div>
          {subscription?.created_at && (
            <div className="text-right">
              <p className="text-sm text-gray-600">Member since</p>
              <p className="text-sm font-medium">
                {new Date(subscription.created_at).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>

        {/* Usage Statistics */}
        {apiUsage && currentTier !== 'free' && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-200">
            <div>
              <p className="text-xs text-gray-600">Requests Today</p>
              <p className="text-lg font-semibold">{apiUsage.requests_today}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">This Month</p>
              <p className="text-lg font-semibold">{apiUsage.requests_this_month}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Rate Limit</p>
              <p className="text-lg font-semibold">{apiUsage.rate_limit_remaining}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Last Request</p>
              <p className="text-sm">
                {apiUsage.last_request ? new Date(apiUsage.last_request).toLocaleDateString() : 'Never'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* API Key Management */}
      {currentTier !== 'free' && (
        <div className="mb-6 p-4 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <Key className="h-5 w-5 text-gray-600 mr-2" />
              <h3 className="font-medium text-gray-900">API Key</h3>
            </div>
            <button
              onClick={generateApiKey}
              disabled={generatingApiKey}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {generatingApiKey ? 'Generating...' : 'Generate New'}
            </button>
          </div>
          <div className="bg-gray-50 p-3 rounded font-mono text-sm">
            {subscription?.api_key ? (
              <span className="text-gray-800">{subscription.api_key}</span>
            ) : (
              <span className="text-gray-500">No API key generated</span>
            )}
          </div>
        </div>
      )}

      {/* Webhook Configuration */}
      {currentTier === 'enterprise' && (
        <div className="mb-6 p-4 border border-gray-200 rounded-lg">
          <div className="flex items-center mb-3">
            <Webhook className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="font-medium text-gray-900">Webhook URL</h3>
          </div>
          <input
            type="url"
            placeholder="https://your-domain.com/webhook"
            defaultValue={subscription?.webhook_url || ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Receive real-time alerts at this URL
          </p>
        </div>
      )}

      {/* Subscription Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(Object.entries(tierFeatures) as [SubscriptionTier, typeof tierFeatures.free][]).map(([tier, config]) => {
          const isCurrentTier = tier === currentTier
          const IconComponent = config.icon

          return (
            <div
              key={tier}
              className={`border rounded-lg p-4 ${
                isCurrentTier 
                  ? `${config.borderColor} ${config.bgColor} border-2` 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-center mb-4">
                <IconComponent className={`h-8 w-8 mx-auto mb-2 ${config.color}`} />
                <h3 className="font-semibold text-gray-900">{config.name}</h3>
                <div className="mt-2">
                  <span className="text-2xl font-bold">{config.price}</span>
                  <span className="text-gray-600 text-sm">/{config.period}</span>
                </div>
              </div>

              <ul className="space-y-2 mb-6">
                {config.features.map((feature, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="text-xs text-gray-600 mb-4">
                <p>Rate Limit: {config.limits.requests_per_hour} req/hour</p>
                <p>WebSocket: {config.limits.websocket_connections} connections</p>
              </div>

              {isCurrentTier ? (
                <div className={`w-full py-2 px-4 text-center text-sm font-medium rounded-md ${config.bgColor} ${config.color} border ${config.borderColor}`}>
                  Current Plan
                </div>
              ) : (
                <button
                  onClick={() => handleUpgrade(tier)}
                  className="w-full py-2 px-4 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  {tier === 'free' ? 'Downgrade' : 'Upgrade'}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}