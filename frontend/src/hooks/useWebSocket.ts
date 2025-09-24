import { useEffect, useRef, useState, useCallback } from 'react'
import { getWebSocketClient, WebSocketMessage, ConnectionStatus, WebSocketEventHandler, ConnectionStatusHandler } from '@/lib/websocket-client'

interface UseWebSocketOptions {
  autoConnect?: boolean
  onMessage?: WebSocketEventHandler
  onConnectionChange?: ConnectionStatusHandler
}

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus
  connect: () => Promise<void>
  disconnect: () => void
  sendMessage: (message: Omit<WebSocketMessage, 'timestamp'>) => void
  isConnected: boolean
  isReconnecting: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, onMessage, onConnectionChange } = options
  
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    reconnecting: false,
    reconnectAttempts: 0
  })
  
  const wsClient = useRef(getWebSocketClient())
  const messageHandlerRef = useRef<WebSocketEventHandler | undefined>(onMessage)
  const connectionHandlerRef = useRef<ConnectionStatusHandler | undefined>(onConnectionChange)
  
  // Update refs when handlers change
  useEffect(() => {
    messageHandlerRef.current = onMessage
  }, [onMessage])
  
  useEffect(() => {
    connectionHandlerRef.current = onConnectionChange
  }, [onConnectionChange])
  
  const connect = useCallback(async () => {
    await wsClient.current.connect()
  }, [])
  
  const disconnect = useCallback(() => {
    wsClient.current.disconnect()
  }, [])
  
  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'timestamp'>) => {
    wsClient.current.send(message)
  }, [])
  
  useEffect(() => {
    const client = wsClient.current
    
    // Set up message handler
    const unsubscribeMessage = client.onMessage((message) => {
      if (messageHandlerRef.current) {
        messageHandlerRef.current(message)
      }
    })
    
    // Set up connection status handler
    const unsubscribeStatus = client.onConnectionStatus((status) => {
      setConnectionStatus(status)
      if (connectionHandlerRef.current) {
        connectionHandlerRef.current(status)
      }
    })
    
    // Auto-connect if enabled
    if (autoConnect) {
      connect()
    }
    
    return () => {
      unsubscribeMessage()
      unsubscribeStatus()
      // Store client reference for cleanup
      const currentClient = client
      if (!autoConnect) {
        currentClient.disconnect()
      }
    }
  }, [autoConnect, connect])
  
  // Cleanup on unmount
  useEffect(() => {
    const client = wsClient.current
    return () => {
      if (!autoConnect) {
        client.disconnect()
      }
    }
  }, [autoConnect])
  
  return {
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    isConnected: connectionStatus.connected,
    isReconnecting: connectionStatus.reconnecting
  }
}

export default useWebSocket