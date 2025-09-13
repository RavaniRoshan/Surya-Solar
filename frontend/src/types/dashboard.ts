export interface AlertData {
  id: string
  timestamp: string
  flare_probability: number
  severity_level: 'low' | 'medium' | 'high'
  alert_triggered: boolean
  message: string
}

export interface CurrentAlertResponse {
  current_probability: number
  severity_level: 'low' | 'medium' | 'high'
  last_updated: string
  next_update: string
  alert_active: boolean
}

export interface HistoricalAlertsResponse {
  alerts: AlertData[]
  total_count: number
  page: number
  page_size: number
  has_more: boolean
}

export interface UserSubscription {
  user_id: string
  tier: 'free' | 'pro' | 'enterprise'
  api_key?: string
  webhook_url?: string
  alert_thresholds: {
    low: number
    medium: number
    high: number
  }
  rate_limits: {
    requests_per_hour: number
    websocket_connections: number
  }
  created_at: string
  updated_at: string
}

export interface ApiUsage {
  total_requests: number
  requests_today: number
  requests_this_month: number
  last_request: string
  rate_limit_remaining: number
}

export type SeverityLevel = 'low' | 'medium' | 'high'
export type SubscriptionTier = 'free' | 'pro' | 'enterprise'

export interface WebSocketAlertMessage {
  type: 'alert'
  data: CurrentAlertResponse
  timestamp: string
}

export interface WebSocketHeartbeatMessage {
  type: 'heartbeat'
  data: { ping?: boolean; pong?: boolean }
  timestamp: string
}

export interface WebSocketErrorMessage {
  type: 'error'
  data: { message: string; code?: string }
  timestamp: string
}

export type WebSocketMessage = WebSocketAlertMessage | WebSocketHeartbeatMessage | WebSocketErrorMessage