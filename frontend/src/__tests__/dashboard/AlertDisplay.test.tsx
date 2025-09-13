import { render, screen, waitFor } from '@testing-library/react'
import { jest } from '@jest/globals'
import AlertDisplay from '@/components/dashboard/AlertDisplay'
import mockApiClient from '../setup/mockApi'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

const mockCurrentAlert = {
  current_probability: 0.35,
  severity_level: 'medium' as const,
  last_updated: '2024-01-15T10:30:00Z',
  next_update: '2024-01-15T10:40:00Z',
  alert_active: true
}

describe('AlertDisplay', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockApiClient.alerts.getCurrent.mockImplementation(() => new Promise(() => {}))
    
    render(<AlertDisplay />)
    
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays current alert data correctly', async () => {
    mockApiClient.alerts.getCurrent.mockResolvedValue({
      data: mockCurrentAlert
    })

    render(<AlertDisplay />)

    await waitFor(() => {
      expect(screen.getByText('Current Solar Weather')).toBeInTheDocument()
    })

    expect(screen.getByText('35.0%')).toBeInTheDocument()
    expect(screen.getByText('Medium Risk')).toBeInTheDocument()
    expect(screen.getByText('ALERT ACTIVE')).toBeInTheDocument()
  })

  it('displays different severity levels with correct styling', async () => {
    const highRiskAlert = {
      ...mockCurrentAlert,
      current_probability: 0.85,
      severity_level: 'high' as const
    }

    mockApiClient.alerts.getCurrent.mockResolvedValue({
      data: highRiskAlert
    })

    render(<AlertDisplay />)

    await waitFor(() => {
      expect(screen.getByText('High Risk')).toBeInTheDocument()
    })

    expect(screen.getByText('85.0%')).toBeInTheDocument()
    expect(screen.getByText('Dangerous solar activity')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockApiClient.alerts.getCurrent.mockRejectedValue(new Error('API Error'))

    render(<AlertDisplay />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load current alert data')).toBeInTheDocument()
    })

    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('formats timestamps correctly', async () => {
    mockApiClient.alerts.getCurrent.mockResolvedValue({
      data: mockCurrentAlert
    })

    render(<AlertDisplay />)

    await waitFor(() => {
      expect(screen.getByText(/Last Updated:/)).toBeInTheDocument()
    })

    expect(screen.getByText(/Next Update:/)).toBeInTheDocument()
  })

  it('shows monitoring status when alert is not active', async () => {
    const inactiveAlert = {
      ...mockCurrentAlert,
      alert_active: false
    }

    mockApiClient.alerts.getCurrent.mockResolvedValue({
      data: inactiveAlert
    })

    render(<AlertDisplay />)

    await waitFor(() => {
      expect(screen.getByText('MONITORING')).toBeInTheDocument()
    })
  })
})