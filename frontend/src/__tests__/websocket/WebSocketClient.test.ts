/**
 * @jest-environment jsdom
 */

import WebSocketClient, { getWebSocketClient } from '@/lib/websocket-client'
import { it } from 'node:test'
import { describe } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { describe } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { describe } from 'node:test'
import { afterEach } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  url: string
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
    // Echo back for testing
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data }))
      }
    }, 5)
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }))
    }
  }

  // Simulate server message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  // Simulate connection error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// Mock Supabase
jest.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: {
      getSession: () => Promise.resolve({
        data: { session: { access_token: 'mock-token' } }
      })
    }
  })
}))

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any

describe('WebSocketClient', () => {
  let client: WebSocketClient
  let mockWs: MockWebSocket

  beforeEach(() => {
    client = new WebSocketClient()
    jest.clearAllMocks()
  })

  afterEach(() => {
    client.disconnect()
  })

  describe('Connection Management', () => {
    it('should connect successfully', async () => {
      const statusHandler = jest.fn()
      client.onConnectionStatus(statusHandler)

      await client.connect()

      // Wait for connection to open
      await new Promise(resolve => setTimeout(resolve, 20))

      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          connected: true,
          reconnecting: false,
          reconnectAttempts: 0
        })
      )
    })

    it('should handle connection errors', async () => {
      const statusHandler = jest.fn()
      client.onConnectionStatus(statusHandler)

      // Mock auth failure
      jest.doMock('@/lib/supabase', () => ({
        createClient: () => ({
          auth: {
            getSession: () => Promise.resolve({ data: { session: null } })
          }
        })
      }))

      await client.connect()

      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          connected: false,
          error: expect.stringContaining('No authentication token')
        })
      )
    })

    it('should disconnect cleanly', async () => {
      const statusHandler = jest.fn()
      client.onConnectionStatus(statusHandler)

      await client.connect()
      await new Promise(resolve => setTimeout(resolve, 20))

      client.disconnect()

      expect(statusHandler).toHaveBeenLastCalledWith(
        expect.objectContaining({
          connected: false,
          reconnecting: false,
          reconnectAttempts: 0
        })
      )
    })
  })

  describe('Message Handling', () => {
    beforeEach(async () => {
      await client.connect()
      await new Promise(resolve => setTimeout(resolve, 20))
      mockWs = (client as any).ws
    })

    it('should receive and parse messages', async () => {
      const messageHandler = jest.fn()
      client.onMessage(messageHandler)

      const testMessage = {
        type: 'alert',
        data: { severity: 'high', probability: 0.8 },
        timestamp: new Date().toISOString()
      }

      mockWs.simulateMessage(testMessage)

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(messageHandler).toHaveBeenCalledWith(testMessage)
    })

    it('should handle heartbeat messages internally', async () => {
      const messageHandler = jest.fn()
      client.onMessage(messageHandler)

      const heartbeatMessage = {
        type: 'heartbeat',
        data: { ping: true },
        timestamp: new Date().toISOString()
      }

      mockWs.simulateMessage(heartbeatMessage)

      await new Promise(resolve => setTimeout(resolve, 10))

      // Heartbeat should not be passed to message handlers
      expect(messageHandler).not.toHaveBeenCalled()
    })

    it('should send messages when connected', async () => {
      const sendSpy = jest.spyOn(mockWs, 'send')

      const message = {
        type: 'alert' as const,
        data: { test: true }
      }

      client.send(message)

      expect(sendSpy).toHaveBeenCalledWith(
        expect.stringContaining('"type":"alert"')
      )
    })

    it('should not send messages when disconnected', () => {
      client.disconnect()

      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation()

      client.send({ type: 'alert', data: {} })

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('WebSocket is not connected'),
        expect.any(Object)
      )

      consoleSpy.mockRestore()
    })
  })

  describe('Reconnection Logic', () => {
    it('should attempt to reconnect on connection loss', async () => {
      const statusHandler = jest.fn()
      client.onConnectionStatus(statusHandler)

      await client.connect()
      await new Promise(resolve => setTimeout(resolve, 20))

      // Simulate connection loss
      mockWs = (client as any).ws
      mockWs.close(1006, 'Connection lost')

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          connected: false,
          reconnecting: true,
          reconnectAttempts: expect.any(Number)
        })
      )
    })

    it('should not reconnect when manually disconnected', async () => {
      const statusHandler = jest.fn()
      client.onConnectionStatus(statusHandler)

      await client.connect()
      await new Promise(resolve => setTimeout(resolve, 20))

      client.disconnect()

      expect(statusHandler).toHaveBeenLastCalledWith(
        expect.objectContaining({
          connected: false,
          reconnecting: false
        })
      )
    })
  })

  describe('Singleton Pattern', () => {
    it('should return the same instance', () => {
      const client1 = getWebSocketClient()
      const client2 = getWebSocketClient()

      expect(client1).toBe(client2)
    })
  })
})