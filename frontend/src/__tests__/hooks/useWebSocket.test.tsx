/**
 * @jest-environment jsdom
 */

import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '@/hooks/useWebSocket'

// Mock the WebSocket client
const mockConnect = jest.fn()
const mockDisconnect = jest.fn()
const mockSend = jest.fn()
const mockOnMessage = jest.fn()
const mockOnConnectionStatus = jest.fn()

jest.mock('@/lib/websocket-client', () => ({
  getWebSocketClient: () => ({
    connect: mockConnect,
    disconnect: mockDisconnect,
    send: mockSend,
    onMessage: mockOnMessage,
    onConnectionStatus: mockOnConnectionStatus,
    getConnectionStatus: () => ({
      connected: false,
      reconnecting: false,
      reconnectAttempts: 0
    })
  })
}))

describe('useWebSocket', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock return functions for event handlers
    mockOnMessage.mockReturnValue(() => {})
    mockOnConnectionStatus.mockReturnValue(() => {})
  })

  it('should auto-connect by default', () => {
    renderHook(() => useWebSocket())

    expect(mockConnect).toHaveBeenCalled()
    expect(mockOnMessage).toHaveBeenCalled()
    expect(mockOnConnectionStatus).toHaveBeenCalled()
  })

  it('should not auto-connect when disabled', () => {
    renderHook(() => useWebSocket({ autoConnect: false }))

    expect(mockConnect).not.toHaveBeenCalled()
  })

  it('should call message handler when provided', () => {
    const messageHandler = jest.fn()
    
    renderHook(() => useWebSocket({ onMessage: messageHandler }))

    expect(mockOnMessage).toHaveBeenCalled()
    
    // Simulate message received
    const messageCallback = mockOnMessage.mock.calls[0][0]
    const testMessage = { type: 'alert', data: {}, timestamp: new Date().toISOString() }
    
    act(() => {
      messageCallback(testMessage)
    })

    expect(messageHandler).toHaveBeenCalledWith(testMessage)
  })

  it('should call connection status handler when provided', () => {
    const statusHandler = jest.fn()
    
    renderHook(() => useWebSocket({ onConnectionChange: statusHandler }))

    expect(mockOnConnectionStatus).toHaveBeenCalled()
    
    // Simulate status change
    const statusCallback = mockOnConnectionStatus.mock.calls[0][0]
    const testStatus = { connected: true, reconnecting: false, reconnectAttempts: 0 }
    
    act(() => {
      statusCallback(testStatus)
    })

    expect(statusHandler).toHaveBeenCalledWith(testStatus)
  })

  it('should provide connect and disconnect functions', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }))

    act(() => {
      result.current.connect()
    })
    expect(mockConnect).toHaveBeenCalled()

    act(() => {
      result.current.disconnect()
    })
    expect(mockDisconnect).toHaveBeenCalled()
  })

  it('should provide sendMessage function', () => {
    const { result } = renderHook(() => useWebSocket())

    const testMessage = { type: 'alert' as const, data: { test: true } }
    
    act(() => {
      result.current.sendMessage(testMessage)
    })

    expect(mockSend).toHaveBeenCalledWith(testMessage)
  })

  it('should update connection status state', () => {
    const { result } = renderHook(() => useWebSocket())

    // Initial state
    expect(result.current.isConnected).toBe(false)
    expect(result.current.isReconnecting).toBe(false)

    // Simulate status change
    const statusCallback = mockOnConnectionStatus.mock.calls[0][0]
    
    act(() => {
      statusCallback({ connected: true, reconnecting: false, reconnectAttempts: 0 })
    })

    expect(result.current.isConnected).toBe(true)
    expect(result.current.isReconnecting).toBe(false)
  })

  it('should cleanup on unmount when autoConnect is false', () => {
    const { unmount } = renderHook(() => useWebSocket({ autoConnect: false }))

    unmount()

    expect(mockDisconnect).toHaveBeenCalled()
  })

  it('should not cleanup on unmount when autoConnect is true', () => {
    const { unmount } = renderHook(() => useWebSocket({ autoConnect: true }))

    unmount()

    // Should not disconnect when autoConnect is true (shared connection)
    expect(mockDisconnect).not.toHaveBeenCalled()
  })
})