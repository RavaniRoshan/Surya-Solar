import { createClient } from './supabase'

export interface WebSocketMessage {
  type: 'alert' | 'heartbeat' | 'error' | 'connection_status'
  data: Record<string, unknown>
  timestamp: string
}

export interface AlertWebSocketMessage extends WebSocketMessage {
  type: 'alert'
  data: {
    current_probability: number
    severity_level: 'low' | 'medium' | 'high'
    last_updated: string
    next_update: string
    alert_active: boolean
    [key: string]: unknown
  }
}

export interface ConnectionStatus {
  connected: boolean
  reconnecting: boolean
  error?: string
  lastConnected?: Date
  reconnectAttempts: number
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void
export type ConnectionStatusHandler = (status: ConnectionStatus) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectInterval: number = 5000
  private maxReconnectAttempts: number = 10
  private reconnectAttempts: number = 0
  private heartbeatInterval: NodeJS.Timeout | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null
  private isManuallyDisconnected: boolean = false
  
  private eventHandlers: Set<WebSocketEventHandler> = new Set()
  private statusHandlers: Set<ConnectionStatusHandler> = new Set()
  
  private connectionStatus: ConnectionStatus = {
    connected: false,
    reconnecting: false,
    reconnectAttempts: 0
  }

  constructor() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = process.env.NEXT_PUBLIC_WS_URL || 
                   process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/^https?:/, wsProtocol) ||
                   `${wsProtocol}//localhost:8000`
    this.url = `${wsHost}/ws/alerts`
  }

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.isManuallyDisconnected = false
    
    try {
      // Get auth token from Supabase
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session?.access_token) {
        throw new Error('No authentication token available')
      }

      // Add token as query parameter
      const wsUrl = `${this.url}?token=${session.access_token}`
      
      this.updateConnectionStatus({
        connected: false,
        reconnecting: this.reconnectAttempts > 0,
        reconnectAttempts: this.reconnectAttempts
      })

      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      this.updateConnectionStatus({
        connected: false,
        reconnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
        reconnectAttempts: this.reconnectAttempts
      })
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    this.isManuallyDisconnected = true
    this.clearReconnectTimeout()
    this.clearHeartbeat()
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }
    
    this.updateConnectionStatus({
      connected: false,
      reconnecting: false,
      reconnectAttempts: 0
    })
  }

  send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const fullMessage: WebSocketMessage = {
        ...message,
        timestamp: new Date().toISOString()
      }
      this.ws.send(JSON.stringify(fullMessage))
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
    }
  }

  onMessage(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.add(handler)
    return () => this.eventHandlers.delete(handler)
  }

  onConnectionStatus(handler: ConnectionStatusHandler): () => void {
    this.statusHandlers.add(handler)
    // Immediately call with current status
    handler(this.connectionStatus)
    return () => this.statusHandlers.delete(handler)
  }

  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus }
  }

  private handleOpen(): void {
    console.log('WebSocket connected')
    this.reconnectAttempts = 0
    this.clearReconnectTimeout()
    
    this.updateConnectionStatus({
      connected: true,
      reconnecting: false,
      lastConnected: new Date(),
      reconnectAttempts: 0
    })
    
    this.startHeartbeat()
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // Handle heartbeat internally
      if (message.type === 'heartbeat') {
        this.send({ type: 'heartbeat', data: { pong: true } })
        return
      }
      
      // Notify all handlers
      this.eventHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('Error in WebSocket message handler:', error)
        }
      })
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason)
    
    this.clearHeartbeat()
    this.ws = null
    
    this.updateConnectionStatus({
      connected: false,
      reconnecting: !this.isManuallyDisconnected && this.reconnectAttempts < this.maxReconnectAttempts,
      error: event.code !== 1000 ? `Connection closed: ${event.reason || 'Unknown reason'}` : undefined,
      reconnectAttempts: this.reconnectAttempts
    })
    
    // Auto-reconnect unless manually disconnected
    if (!this.isManuallyDisconnected) {
      this.scheduleReconnect()
    }
  }

  private handleError(error: Event): void {
    console.error('WebSocket error:', error)
    
    this.updateConnectionStatus({
      connected: false,
      reconnecting: false,
      error: 'WebSocket connection error',
      reconnectAttempts: this.reconnectAttempts
    })
  }

  private scheduleReconnect(): void {
    if (this.isManuallyDisconnected || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return
    }
    
    this.clearReconnectTimeout()
    
    // Exponential backoff with jitter
    const baseDelay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts), 30000)
    const jitter = Math.random() * 1000
    const delay = baseDelay + jitter
    
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  private startHeartbeat(): void {
    this.clearHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'heartbeat', data: { ping: true } })
      }
    }, 30000) // Send heartbeat every 30 seconds
  }

  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
  }

  private updateConnectionStatus(status: Partial<ConnectionStatus>): void {
    this.connectionStatus = { ...this.connectionStatus, ...status }
    
    // Notify all status handlers
    this.statusHandlers.forEach(handler => {
      try {
        handler(this.connectionStatus)
      } catch (error) {
        console.error('Error in connection status handler:', error)
      }
    })
  }
}

// Singleton instance
let wsClient: WebSocketClient | null = null

export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient()
  }
  return wsClient
}

export default WebSocketClient