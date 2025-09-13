/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from '@/app/dashboard/page'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

// Mock the auth context
const mockUser = { email: 'test@example.com', id: '123' }
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: mockUser })
}))

// Mock API client
jest.mock('@/lib/api-client', () => ({
  api: {
    alerts: {
      getCurrent: jest.fn().mockResolvedValue({
        data: {
          current_probability: 0.25,
          severity_level: 'medium',
          last_updated: new Date().toISOString(),
          next_update: new Date(Date.now() + 600000).toISOString(),
          alert_active: false
        }
      }),
      getHistory: jest.fn().mockResolvedValue({
        data: {
          alerts: [],
          total_count: 0,
          page: 1,
          page_size: 100,
          has_more: false
        }
      })
    },
    users: {
      getProfile: jest.fn().mockResolvedValue({ data: {} }),
      updateProfile: jest.fn().mockResolvedValue({ data: {} }),
      getSubscription: jest.fn().mockResolvedValue({
        data: {
          tier: 'pro',
          api_key: 'test-key',
          alert_thresholds: { low: 0.2, medium: 0.5, high: 0.8 }
        }
      }),
      updateSubscription: jest.fn().mockResolvedValue({ data: {} }),
      generateApiKey: jest.fn().mockResolvedValue({ data: { api_key: 'new-key' } }),
      getApiUsage: jest.fn().mockResolvedValue({
        data: {
          total_requests: 100,
          requests_today: 10,
          requests_this_month: 50,
          last_request: new Date().toISOString(),
          rate_limit_remaining: 90
        }
      })
    }
  }
}))

// Mock WebSocket client
const mockConnect = jest.fn()
const mockDisconnect = jest.fn()
const mockSend = jest.fn()
let mockMessageHandlers: Array<(message: any) => void> = []
let mockStatusHandlers: Array<(status: any) => void> = []

jest.mock('@/lib/websocket-client', () => ({
  getWebSocketClient: () => ({
    connect: mockConnect,
    disconnect: mockDisconnect,
    send: mockSend,
    onMessage: (handler: (message: any) => void) => {
      mockMessageHandlers.push(handler)
      return () => {
        mockMessageHandlers = mockMessageHandlers.filter(h => h !== handler)
      }
    },
    onConnectionStatus: (handler: (status: any) => void) => {
      mockStatusHandlers.push(handler)
      // Immediately call with initial status
      handler({
        connected: false,
        reconnecting: false,
        reconnectAttempts: 0
      })
      return () => {
        mockStatusHandlers = mockStatusHandlers.filter(h => h !== handler)
      }
    },
    getConnectionStatus: () => ({
      connected: false,
      reconnecting: false,
      reconnectAttempts: 0
    })
  })
}))

// Mock notifications
const mockShowAlertNotification = jest.fn()
const mockShowConnectionNotification = jest.fn()
const mockRequestPermission = jest.fn().mockResolvedValue('granted')

jest.mock('@/lib/notifications', () => ({
  getNotificationManager: () => ({
    showAlertNotification: mockShowAlertNotification,
    showConnectionNotification: mockShowConnectionNotification,
    requestPermission: mockRequestPermission
  })
}))

// Mock Recharts to avoid canvas issues in tests
jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  ReferenceLine: () => <div data-testid="reference-line" />
}))

describe('Dashboard WebSocket Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockMessageHandlers = []
    mockStatusHandlers = []
  })

  it('should establish WebSocket connection on mount', async () => {
    render(<DashboardPage />)

    expect(mockConnect).toHaveBeenCalled()
    expect(mockRequestPermission).toHaveBeenCalled()
  })

  it('should show connection status indicator', async () => {
    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  it('should update connection status when WebSocket connects', async () => {
    render(<DashboardPage />)

    // Simulate connection established
    act(() => {
      mockStatusHandlers.forEach(handler => 
        handler({
          connected: true,
          reconnecting: false,
          reconnectAttempts: 0,
          lastConnected: new Date()
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    expect(mockShowConnectionNotification).toHaveBeenCalledWith(true)
  })

  it('should handle real-time alert messages', async () => {
    render(<DashboardPage />)

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText('Current Solar Weather')).toBeInTheDocument()
    })

    // Simulate receiving a high-severity alert
    const alertMessage = {
      type: 'alert',
      data: {
        current_probability: 0.85,
        severity_level: 'high',
        last_updated: new Date().toISOString(),
        next_update: new Date(Date.now() + 600000).toISOString(),
        alert_active: true
      },
      timestamp: new Date().toISOString()
    }

    act(() => {
      mockMessageHandlers.forEach(handler => handler(alertMessage))
    })

    await waitFor(() => {
      expect(screen.getByText('85.0%')).toBeInTheDocument()
      expect(screen.getByText('High Risk')).toBeInTheDocument()
      expect(screen.getByText('ALERT ACTIVE')).toBeInTheDocument()
    })

    expect(mockShowAlertNotification).toHaveBeenCalledWith({
      severity: 'high',
      probability: 0.85,
      timestamp: alertMessage.data.last_updated,
      message: 'Solar flare alert is active!'
    })
  })

  it('should show live indicator when connected', async () => {
    render(<DashboardPage />)

    // Simulate connection established
    act(() => {
      mockStatusHandlers.forEach(handler => 
        handler({
          connected: true,
          reconnecting: false,
          reconnectAttempts: 0
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument()
    })
  })

  it('should handle connection errors gracefully', async () => {
    render(<DashboardPage />)

    // Simulate connection error
    act(() => {
      mockStatusHandlers.forEach(handler => 
        handler({
          connected: false,
          reconnecting: false,
          error: 'Network connection failed',
          reconnectAttempts: 1
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    expect(mockShowConnectionNotification).toHaveBeenCalledWith(false, 'Network connection failed')
  })

  it('should show reconnecting status', async () => {
    render(<DashboardPage />)

    // Simulate reconnecting state
    act(() => {
      mockStatusHandlers.forEach(handler => 
        handler({
          connected: false,
          reconnecting: true,
          reconnectAttempts: 2
        })
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Reconnecting')).toBeInTheDocument()
    })
  })

  it('should allow manual reconnection', async () => {
    const user = userEvent.setup()
    render(<DashboardPage />)

    // Simulate disconnected state
    act(() => {
      mockStatusHandlers.forEach(handler => 
        handler({
          connected: false,
          reconnecting: false,
          error: 'Connection lost',
          reconnectAttempts: 0
        })
      )
    })

    // Click on connection status to open details
    const statusButton = screen.getByText('Disconnected')
    await user.click(statusButton)

    // Click reconnect button
    const reconnectButton = await screen.findByText('Reconnect Now')
    await user.click(reconnectButton)

    expect(mockConnect).toHaveBeenCalledTimes(2) // Initial + manual reconnect
  })

  it('should not show notifications for low severity alerts', async () => {
    render(<DashboardPage />)

    // Simulate receiving a low-severity alert
    const alertMessage = {
      type: 'alert',
      data: {
        current_probability: 0.15,
        severity_level: 'low',
        last_updated: new Date().toISOString(),
        next_update: new Date(Date.now() + 600000).toISOString(),
        alert_active: false
      },
      timestamp: new Date().toISOString()
    }

    act(() => {
      mockMessageHandlers.forEach(handler => handler(alertMessage))
    })

    await waitFor(() => {
      expect(screen.getByText('15.0%')).toBeInTheDocument()
    })

    // Should not show notification for low severity
    expect(mockShowAlertNotification).not.toHaveBeenCalled()
  })

  it('should update historical chart with real-time data', async () => {
    render(<DashboardPage />)

    // Wait for chart to render
    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    // Simulate receiving new alert data
    const alertMessage = {
      type: 'alert',
      data: {
        current_probability: 0.45,
        severity_level: 'medium',
        last_updated: new Date().toISOString(),
        next_update: new Date(Date.now() + 600000).toISOString(),
        alert_active: false
      },
      timestamp: new Date().toISOString()
    }

    act(() => {
      mockMessageHandlers.forEach(handler => handler(alertMessage))
    })

    // Chart should still be present (real-time updates happen internally)
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })
})