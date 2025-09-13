/**
 * @jest-environment jsdom
 */

import NotificationManager, { getNotificationManager } from '@/lib/notifications'

// Mock Notification API
class MockNotification {
  static permission: NotificationPermission = 'default'
  static requestPermission = jest.fn()

  title: string
  options: NotificationOptions
  close = jest.fn()

  constructor(title: string, options?: NotificationOptions) {
    this.title = title
    this.options = options || {}
  }

  static mockGrantPermission() {
    MockNotification.permission = 'granted'
    MockNotification.requestPermission.mockResolvedValue('granted')
  }

  static mockDenyPermission() {
    MockNotification.permission = 'denied'
    MockNotification.requestPermission.mockResolvedValue('denied')
  }

  static reset() {
    MockNotification.permission = 'default'
    MockNotification.requestPermission.mockReset()
  }
}

// Replace global Notification with mock
Object.defineProperty(global, 'Notification', {
  value: MockNotification,
  writable: true
})

describe('NotificationManager', () => {
  let manager: NotificationManager

  beforeEach(() => {
    manager = new NotificationManager()
    MockNotification.reset()
  })

  describe('Permission Management', () => {
    it('should request notification permission', async () => {
      MockNotification.mockGrantPermission()

      const permission = await manager.requestPermission()

      expect(MockNotification.requestPermission).toHaveBeenCalled()
      expect(permission).toBe('granted')
    })

    it('should handle permission denial', async () => {
      MockNotification.mockDenyPermission()

      const permission = await manager.requestPermission()

      expect(permission).toBe('denied')
      expect(manager.canShowNotifications()).toBe(false)
    })

    it('should return existing permission if already granted', async () => {
      MockNotification.mockGrantPermission()

      const permission = await manager.requestPermission()

      expect(permission).toBe('granted')
      expect(manager.canShowNotifications()).toBe(true)
    })
  })

  describe('Basic Notifications', () => {
    beforeEach(() => {
      MockNotification.mockGrantPermission()
    })

    it('should show basic notification', () => {
      const notification = manager.showNotification({
        title: 'Test Title',
        body: 'Test Body'
      })

      expect(notification).toBeInstanceOf(MockNotification)
      expect(notification?.title).toBe('Test Title')
      expect(notification?.options.body).toBe('Test Body')
    })

    it('should not show notification without permission', () => {
      MockNotification.mockDenyPermission()
      manager = new NotificationManager()

      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation()

      const notification = manager.showNotification({
        title: 'Test',
        body: 'Test'
      })

      expect(notification).toBeNull()
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Cannot show notification')
      )

      consoleSpy.mockRestore()
    })
  })

  describe('Alert Notifications', () => {
    beforeEach(() => {
      MockNotification.mockGrantPermission()
    })

    it('should show low severity alert notification', () => {
      const notification = manager.showAlertNotification({
        severity: 'low',
        probability: 0.15,
        timestamp: new Date().toISOString()
      })

      expect(notification).toBeInstanceOf(MockNotification)
      expect(notification?.title).toContain('Low Solar Activity')
      expect(notification?.options.body).toContain('15.0%')
      expect(notification?.options.silent).toBe(true)
    })

    it('should show medium severity alert notification', () => {
      const notification = manager.showAlertNotification({
        severity: 'medium',
        probability: 0.45,
        timestamp: new Date().toISOString()
      })

      expect(notification?.title).toContain('Medium Solar Activity Alert')
      expect(notification?.options.body).toContain('45.0%')
      expect(notification?.options.requireInteraction).toBe(true)
    })

    it('should show high severity alert notification', () => {
      const notification = manager.showAlertNotification({
        severity: 'high',
        probability: 0.85,
        timestamp: new Date().toISOString(),
        message: 'Critical alert!'
      })

      expect(notification?.title).toContain('HIGH SOLAR ACTIVITY ALERT')
      expect(notification?.options.body).toContain('Critical alert!')
      expect(notification?.options.requireInteraction).toBe(true)
    })
  })

  describe('Connection Notifications', () => {
    beforeEach(() => {
      MockNotification.mockGrantPermission()
    })

    it('should show connection established notification', () => {
      const notification = manager.showConnectionNotification(true)

      expect(notification?.title).toContain('ZERO-COMP Connected')
      expect(notification?.options.body).toContain('Real-time solar weather monitoring is active')
      expect(notification?.options.silent).toBe(true)
    })

    it('should show connection lost notification', () => {
      const notification = manager.showConnectionNotification(false, 'Network error')

      expect(notification?.title).toContain('ZERO-COMP Disconnected')
      expect(notification?.options.body).toContain('Network error')
    })
  })

  describe('System Notifications', () => {
    beforeEach(() => {
      MockNotification.mockGrantPermission()
    })

    it('should show info notification', () => {
      const notification = manager.showSystemNotification('Info', 'Information message', 'info')

      expect(notification?.title).toContain('💡 Info')
      expect(notification?.options.body).toBe('Information message')
      expect(notification?.options.requireInteraction).toBe(false)
    })

    it('should show warning notification', () => {
      const notification = manager.showSystemNotification('Warning', 'Warning message', 'warning')

      expect(notification?.title).toContain('⚠️ Warning')
      expect(notification?.options.requireInteraction).toBe(false)
    })

    it('should show error notification', () => {
      const notification = manager.showSystemNotification('Error', 'Error message', 'error')

      expect(notification?.title).toContain('❌ Error')
      expect(notification?.options.requireInteraction).toBe(true)
    })
  })

  describe('Singleton Pattern', () => {
    it('should return the same instance', () => {
      const manager1 = getNotificationManager()
      const manager2 = getNotificationManager()

      expect(manager1).toBe(manager2)
    })
  })
})